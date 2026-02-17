"""
Recommendation service – matches user profiles against
government schemes using RAG retrieval + LLM analysis.

Implements a Researcher-Critic agentic loop: the initial retrieval is
evaluated by a "Critic" LLM call that checks **topic relevance only**.
If the context is deemed irrelevant the Critic suggests a refined query
and the loop retries (up to 3 times).
"""

import json
import re

from backend.app.services.rag_retriever import RAGService
from backend.app.services.llm_engine import LLMEngine
from backend.app.models.dtos import UserProfile

# ── Prompt templates ─────────────────────────────────────

_ELIGIBILITY_PROMPT = """\
You are a helpful Government Scheme Advisor for India.

User Profile: {profile}

Below are excerpts from various government scheme guidelines:
{context}

Your job: Identify ALL schemes from the above context that this user is
eligible for, based on their occupation, income, age, state, and caste.

Key rules:
- Central / National schemes (names starting with PM, Pradhan Mantri, or
  National) are available to ALL states. Always include them if the user
  meets the other criteria (occupation, income, age).
- If a scheme has no caste restriction mentioned, it is open to all castes.
- If occupation matches (e.g., user is a Farmer and scheme is for Farmers),
  include it.
- If income is within the limit (or no limit is stated), include it.
- Only EXCLUDE a scheme if it clearly does NOT apply (e.g., a scheme
  exclusively for SC/ST when user is OBC, or a scheme exclusively for
  a different state).
- When in doubt, INCLUDE the scheme.

{negative_constraint}

Output: Return a JSON array. Each object must have:
- "scheme_name": string (the name of the scheme)
- "eligibility_status": "Eligible" (always in English for parsing)
- "reason": A short confident explanation of why the user qualifies.

Language: Translate the "reason" field into {language}. Keep "scheme_name"
and "eligibility_status" in English. If the language is English, just write
normally.

If you cannot find any matching scheme, return: []

IMPORTANT: Return ONLY the JSON array. Do not output any conversational
text, notes, or explanations before or after the JSON. Your entire
response must start with [ and end with ]. Nothing else."""


class RecommendationService:
    """Generate personalised scheme recommendations for a user profile."""

    def __init__(self) -> None:
        self.rag_service = RAGService()
        self.llm_engine = LLMEngine()

    # ── Public entry point ───────────────────────────────

    def get_eligible_schemes(self, profile: UserProfile) -> list[dict]:
        """Researcher-Critic agentic loop with deep logging."""

        print(f"\n🕵️‍♂️ AGENT START: Processing {profile.occupation} "
              f"from {profile.state}")

        # Initial search query
        current_query = (
            f"Government schemes for {profile.occupation} "
            f"{profile.state} benefits"
        )
        unique_docs = []
        seen_content: set[str] = set()

        for attempt in range(3):
            print(f"\n🔄 ATTEMPT {attempt + 1}: Searching for: "
                  f"'{current_query}'")

            # ── 1. Retrieve ──────────────────────────────
            docs = self.rag_service.get_raw_docs(current_query, k=20)
            print(f"   📦 Found {len(docs)} raw docs from Pinecone")

            # ── 2. Python State Filter ───────────────────
            filtered_docs = []
            user_state_norm = profile.state.strip().lower()
            for doc in docs:
                doc_state = (
                    doc.metadata.get("state") or ""
                ).strip().lower()
                if (not doc_state
                        or doc_state == "central"
                        or doc_state == user_state_norm):
                    if doc.page_content not in seen_content:
                        filtered_docs.append(doc)
                        seen_content.add(doc.page_content)

            print(f"   🔍 Kept {len(filtered_docs)} new docs after "
                  f"State Filter (total unique so far: "
                  f"{len(unique_docs) + len(filtered_docs)})")

            if not filtered_docs:
                print("   ⚠️ No docs passed the State Filter. "
                      "Forcing broader query.")
                current_query = (
                    f"Government schemes for {profile.occupation} India"
                )
                continue

            # ── 3. Critic (Topic Relevance Only) ─────────
            critic_context = "\n".join(
                d.page_content[:200] for d in filtered_docs[:5]
            )
            critic_prompt = (
                f"You are a Relevance Filter. "
                f"The user is a {profile.occupation}.\n\n"
                f"Retrieved Context Snippets:\n{critic_context}\n\n"
                f"Does this context contain ANY schemes related to "
                f"the user's occupation ('{profile.occupation}')?\n\n"
                f"If YES (even if State/Income/Caste doesn't match "
                f"perfectly): Return {{\"status\": \"PASS\"}}\n"
                f"If NO (completely irrelevant topics, e.g., farming "
                f"schemes for a student): Return {{\"status\": \"FAIL\", "
                f"\"suggested_query\": \"a better search query\"}}\n\n"
                f"Do NOT filter based on Eligibility. Only filter "
                f"based on Topic Relevance.\n"
                f"Return ONLY valid JSON, nothing else."
            )

            raw_critic = self.llm_engine.generate_raw(critic_prompt)
            print(f"   🤖 CRITIC SAYS: {raw_critic}")

            # ── 4. Parse Critic verdict ──────────────────
            if '"status": "PASS"' in raw_critic or "PASS" in raw_critic:
                print("   ✅ Critic Approved. Breaking loop.")
                unique_docs.extend(filtered_docs)
                break
            else:
                print("   ❌ Critic Rejected. Retrying with broader "
                      "query...")
                unique_docs.extend(filtered_docs)  # keep what we found

                # Try to extract Critic's suggested query
                suggested = self._extract_suggested_query(raw_critic)
                if suggested:
                    current_query = suggested
                    print(f"   💡 Using Critic's suggestion: "
                          f"'{current_query}'")
                else:
                    current_query = (
                        f"List of all government schemes for "
                        f"{profile.occupation} in India"
                    )
                    print(f"   💡 Using fallback query: '{current_query}'")
        else:
            # Loop exhausted without PASS – use whatever we collected
            print("   ⚠️ Max retries reached. Proceeding with "
                  f"{len(unique_docs)} collected docs.")

        # ── 5. Generate final verdicts ───────────────────
        print(f"\n📝 GENERATING VERDICTS with {len(unique_docs)} docs")
        return self._generate_verdicts(profile, unique_docs)

    # ── Private helpers ──────────────────────────────────

    def _extract_suggested_query(self, raw_critic: str) -> str | None:
        """Try to pull suggested_query from the Critic's JSON."""
        try:
            obj = json.loads(raw_critic)
            return obj.get("suggested_query")
        except json.JSONDecodeError:
            json_str = self._extract_json_object(raw_critic)
            if json_str:
                try:
                    obj = json.loads(json_str)
                    return obj.get("suggested_query")
                except json.JSONDecodeError:
                    pass
        return None

    def _generate_verdicts(
        self, profile: UserProfile, docs: list
    ) -> list[dict]:
        """Build the eligibility prompt, call the LLM, and parse results."""
        if not docs:
            print("   ⚠️ No docs to analyse – returning empty list")
            return [{
                "scheme_name": "No Schemes Found",
                "eligibility_status": "Eligible",
                "reason": (
                    "We could not find relevant scheme documents. "
                    "Please try different profile details."
                ),
            }]

        top_docs = docs[:10]
        context = "\n\n".join(doc.page_content for doc in top_docs)

        negative_constraint = ""
        if profile.caste:
            negative_constraint = (
                f"Note: The user's caste category is '{profile.caste}'. "
                f"Exclude schemes that are strictly reserved for a "
                f"different caste category (e.g., do not include "
                f"SC/ST-only schemes for an OBC user). Schemes open "
                f"to all categories should be included."
            )

        analysis_prompt = _ELIGIBILITY_PROMPT.format(
            profile=profile.model_dump(),
            context=context,
            negative_constraint=negative_constraint,
            language=profile.language,
        )

        raw_response = self.llm_engine.generate_raw(analysis_prompt)
        print(f"   📨 Raw LLM response = {raw_response[:500]}")
        return self._parse_response(raw_response)

    # ── JSON extraction / parsing ────────────────────────

    @staticmethod
    def _extract_json_object(text: str) -> str | None:
        """Find the first balanced JSON object { ... } in text."""
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        in_string = False
        escape_next = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape_next:
                escape_next = False
                continue
            if ch == "\\" and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        return None

    @staticmethod
    def _extract_json_array(text: str) -> str | None:
        """Find the first balanced JSON array in *text* using bracket counting."""
        start = text.find("[")
        if start == -1:
            return None
        depth = 0
        in_string = False
        escape_next = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape_next:
                escape_next = False
                continue
            if ch == "\\" and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        return None

    @staticmethod
    def _parse_response(raw: str) -> list[dict]:
        """Best-effort extraction of a JSON array from the LLM output."""
        # Try direct parse first
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except json.JSONDecodeError:
            pass

        # Use bracket-counting to extract the first balanced JSON array
        json_str = RecommendationService._extract_json_array(raw)
        if json_str:
            try:
                parsed = json.loads(json_str)
                return parsed if isinstance(parsed, list) else [parsed]
            except json.JSONDecodeError:
                pass

        # Fallback – return the raw text wrapped in a single verdict
        return [{
            "scheme_name": "Analysis",
            "eligibility_status": "Eligible",
            "reason": raw,
        }]
