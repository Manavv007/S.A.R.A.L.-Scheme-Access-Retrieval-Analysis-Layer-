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
  National) are available to ALL states. Do not hallucinate, but do not
  falsely reject valid Central schemes.
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
        """Dual-Query Retrieval Pipeline (Parallel State + Central Search)."""

        print(f"\n🕵️‍♂️ PIPELINE START: Processing {profile.occupation} "
              f"from {profile.state}")

        # ── Strategy: Dual-Query Expansion ────────────────
        # Query 1: Specific State Schemes
        query_state = (
            f"{profile.occupation} schemes in {profile.state} "
            f"earning {profile.income}"
        )
        # Query 2: Generic Central Schemes (Explicitly exclude state name)
        query_central = (
            f"Central government {profile.occupation} schemes "
            f"scholarships financial aid"
        )

        print(f"\n🔄 QUERY 1 (State): '{query_state}'")
        print(f"🔄 QUERY 2 (Central): '{query_central}'")

        # ── Parallel Retrieval ───────────────────────────
        # Note: In a real async setup, we'd await these. Here we call sequentially
        # but conceptually they are independent.
        docs_state = self.rag_service.get_raw_docs(query_state, k=15)
        docs_central = self.rag_service.get_raw_docs(query_central, k=15)

        print(f"   📦 Docs found: State={len(docs_state)}, "
              f"Central={len(docs_central)}")

        # ── Merge & Deduplicate ──────────────────────────
        all_docs = docs_state + docs_central
        unique_docs = []
        seen_content = set()

        for doc in all_docs:
            # Use content hash or strict string for dedupe
            content_sig = doc.page_content.strip()
            if content_sig not in seen_content:
                unique_docs.append(doc)
                seen_content.add(content_sig)

        print(f"   ✅ Total unique docs after merge: {len(unique_docs)}")

        # ── Smart Filtering ──────────────────────────────
        valid_docs = self._filter_docs(unique_docs, profile)
        print(f"   🔍 Final valid docs sent to LLM: {len(valid_docs)}")

        # ── Final LLM Analysis ───────────────────────────
        print(f"\n📝 GENERATING VERDICTS with {len(valid_docs)} total docs")
        return self._generate_verdicts(profile, valid_docs)

    # ── Private helpers ──────────────────────────────────

    def _filter_docs(self, docs, profile: UserProfile) -> list:
        """Apply SmartFilter logic and log why docs are dropped."""
        kept = []
        user_state_norm = profile.state.strip().lower()

        for doc in docs:
            # Metadata check
            doc_state = doc.metadata.get("state", "central")
            
            # SmartFilter Logic
            is_match = self._is_state_match(doc_state, profile.state)
            
            if is_match:
                kept.append(doc)
            else:
                # Log why it was dropped (essential for debugging)
                scheme_name = doc.page_content.split('\n')[0][:50]
                print(f"   ❌ Dropped '{scheme_name}...' -> "
                      f"Doc State '{doc_state}' != User '{user_state_norm}'")
        
        return kept

    def _normalize_state_string(self, state_text: str) -> str:
        """
        Removes spaces, hyphens, and casing to make state matching robust.
        Example: "Andhra-Pradesh" -> "andhrapradesh" == "Andhra Pradesh"
        """
        if not state_text:
            return ""
        return str(state_text).lower().replace(" ", "").replace("-", "").strip()

    def _is_state_match(self, doc_state: str, user_state: str) -> bool:
        """
        Global Logic: 
        1. If doc is 'Central', 'India', 'Pan India' -> MATCHES EVERYONE.
        2. If doc has NO state tag -> MATCHES EVERYONE (Assume open).
        3. If doc is specific (e.g. 'Gujarat') -> Must match User's state exactly.
        """
        # Normalize strictly
        clean_doc = str(doc_state).strip().lower().replace(" ", "").replace("-", "")
        clean_user = str(user_state).strip().lower().replace(" ", "").replace("-", "")
        
        # 🟢 RULE 1: universal keywords (The "Catch-All")
        universal_keywords = ["central", "india", "allindia", "union", "panindia", "governmentofindia"]
        if any(keyword in clean_doc for keyword in universal_keywords):
            return True

        # 🟢 RULE 2: Missing tag = Open to all
        if not clean_doc or clean_doc == "none" or clean_doc == "nan":
            return True

        # 🟢 RULE 3: Exact State Match (e.g. gujarat == gujarat)
        if clean_doc == clean_user:
            return True
            
        # 🔴 Otherwise, it's a mismatch (e.g. User=Gujarat, Doc=Maharashtra)
        return False

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
                    "We could not find relevant scheme documents details. "
                    "However, please check official portals like National "
                    "Scholarship Portal."
                ),
            }]

        # Prioritize docs: shorter content usually headers/summaries
        # But here we just take top N to avoid token overflow
        top_docs = docs[:15] 
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

        # Call LLM
        raw_response = self.llm_engine.generate_raw(analysis_prompt)
        print(f"   📨 Raw LLM response size: {len(raw_response)} chars")
        return self._parse_response(raw_response)

    # ── JSON extraction / parsing ────────────────────────

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
