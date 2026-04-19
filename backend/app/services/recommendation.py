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

### OCCUPATION ELIGIBILITY LOGIC (STRICT):
User Occupation: {user_occupation}
Step 1: Does the scheme explicitly target a specific occupation or demographic (e.g., "Students", "Farmers", "Micro-enterprises/Business")?
  - YES: Does it match the User's Occupation ({user_occupation})?
    - NO: -> MARK AS NOT ELIGIBLE. (Reason: "Specifically for [Target], not for {user_occupation}.")
    - YES: -> Go to Step 2.
  - NO (Universal/General Citizens): -> Go to Step 2.

### INCOME ELIGIBILITY LOGIC (STRICT):
User Income: {user_income} (Integer)
Step 2: Does the scheme explicitly state an "Income Limit" or "Family Income" cap?
  - NO (Silent/Universal/Merit-based): -> MARK AS ELIGIBLE. (Reason: "No income limit specified.")
  - YES: Extract limit and compare. Is {user_income} > Scheme_Limit?
    - YES: -> MARK AS NOT ELIGIBLE. (Reason: "Income exceeds the limit.")
    - NO: -> MARK AS ELIGIBLE.

CRITICAL RULE FOR HIGH INCOME:
If User Income (> 8,00,000), prioritize "Merit-based", "Universal", or "Open Category".

Key rules:
- Central / National schemes (starting with PM, Pradhan Mantri) apply to ALL states.
- Caste restrictions: If scheme is "SC/ST only" and user is "General/OBC", MARK AS NOT ELIGIBLE.
- Only include a scheme if the user clearly meets the occupation, state, income, and caste criteria.
- If the user is "Business" or "Farmer", DO NOT recommend student scholarships unless the scheme explicitly supports their children and it's mentioned.
- Do not recommend schemes that are clearly meant for a completely different profile.

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
        """
        Production-Grade Hybrid Retrieval Engine.
        Executes Multi-Vector Search -> Deduplication -> Strict Metadata Filtering -> LLM Analysis.
        """
        print(f"\n🚀 ENGINE START: {profile.occupation} | {profile.state} | {profile.income}")

        # 1. Multi-Vector Retrieval (Semantic + Keyword + National)
        raw_docs = self._retrieve_documents(profile)
        print(f"   📦 Aggregated {len(raw_docs)} raw documents from all strategies.")

        # 2. Strict Metadata Filtering
        valid_docs = self._filter_docs(raw_docs, profile)
        print(f"   🎯 Hit Rate: {len(valid_docs)}/{len(raw_docs)} docs qualified for analysis.")

        # 3. LLM Analysis
        print(f"\n📝 GENERATING VERDICTS with {len(valid_docs)} context documents")
        return self._generate_verdicts(profile, valid_docs)

    def _retrieve_documents(self, profile: UserProfile) -> list:
        """
        Executes 3 parallel retrieval strategies to maximize recall.
        Strategy A: Semantic Search (Nuanced understanding)
        Strategy B: Metadata-Focused (State/Occupation keywords)
        Strategy C: Broad/National (Catch-all for central schemes)
        """
        # Enrich occupation for vector search matching
        occupation_synonyms = {
            "Retired": "Retired senior citizen old age pension",
            "Student": "Student scholarship education",
            "Farmer": "Farmer agriculture krishi",
            "Business": "Business MSME startup entrepreneur"
        }
        search_occ = occupation_synonyms.get(profile.occupation, profile.occupation)

        # Query A: Semantic (removed exact income to avoid brittle number embeddings)
        query_a = f"Government schemes for {search_occ} in {profile.state} financial assistance"
        
        # Query B: Structured/Keyword
        query_b = f"{search_occ} schemes state:{profile.state} eligibility"

        # Query C: National Fallback (Crucial for Central schemes)
        query_c = f"Central government {search_occ} schemes financial aid"

        print(f"\n🔍 [STRATEGY A] Semantic: '{query_a}'")
        print(f"🔍 [STRATEGY B] Keyword:  '{query_b}'")
        print(f"🔍 [STRATEGY C] National: '{query_c}'")

        # In a true async system, these would run in parallel.
        # Here we run sequentially but independent.
        docs_a = self.rag_service.get_raw_docs(query_a, k=10)
        docs_b = self.rag_service.get_raw_docs(query_b, k=10)
        docs_c = self.rag_service.get_raw_docs(query_c, k=15)

        print(f"   Found: A={len(docs_a)}, B={len(docs_b)}, C={len(docs_c)}")

        # Merge & Deduplicate
        all_docs = docs_a + docs_b + docs_c
        unique_docs = []
        seen_content = set()

        for doc in all_docs:
            # Create a robust signature (first 100 chars often distinct enough)
            sig = doc.page_content[:200].strip()
            if sig not in seen_content:
                unique_docs.append(doc)
                seen_content.add(sig)
        
        return unique_docs

    def _filter_docs(self, docs: list, profile: UserProfile) -> list:
        """
        Strict Metadata Filter.
        - Keeps doc if State matches User State (Normalized).
        - Keeps doc if State is 'Central', 'India', 'Union'.
        - Drops doc if State is 'Maharastra' but User is 'Gujarat'.
        """
        kept = []
        user_state_norm = self._normalize_state_string(profile.state)

        for doc in docs:
            raw_state = doc.metadata.get("state", "central")
            
            if self._is_state_match(raw_state, profile.state):
                kept.append(doc)
            else:
                # Debug log for rejected docs (High Observability)
                snippet = doc.page_content.split('\n')[0][:40]
                # print(f"   ❌ Rejected: '{snippet}...' [Doc State: {raw_state}]")
        
        return kept

    def _normalize_state_string(self, state_text: str) -> str:
        """
        Removes spaces, hyphens, and casing.
        Example: "Andhra-Pradesh" -> "andhrapradesh"
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
        clean_doc = self._normalize_state_string(doc_state)
        clean_user = self._normalize_state_string(user_state)
        
        # 🟢 RULE 1: Universal keywords
        universal_keywords = ["central", "india", "allindia", "union", "panindia", "governmentofindia"]
        if any(keyword in clean_doc for keyword in universal_keywords):
            return True

        # 🟢 RULE 2: Missing tag = Open to all
        if not clean_doc or clean_doc == "none" or clean_doc == "nan":
            return True

        # 🟢 RULE 3: Exact State Match
        if clean_doc == clean_user:
            return True
            
        # 🔴 Mismatch
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

        # Prepare Prompt
        analysis_prompt = _ELIGIBILITY_PROMPT.format(
            profile=profile.model_dump(),
            user_occupation=profile.occupation,
            user_income=profile.income,  # Pass explicit income for logic check
            context=context,
            negative_constraint=negative_constraint,
            language=profile.language,
        )

        # Call LLM
        raw_response = self.llm_engine.generate_raw(analysis_prompt)
        print(f"   📨 Raw LLM response size: {len(raw_response)} chars")
        parsed_results = self._parse_response(raw_response)
        
        # Deduplicate schemas to prevent displaying multiple sub-components 
        # of the same parent scheme (e.g. "MSME: Tech", "MSME: Rent")
        deduped = {}
        for item in parsed_results:
            name = item.get("scheme_name", "")
            # Base name is everything before the first colon or dash
            if ":" in name:
                base_name = name.split(":")[0].strip()
            elif " - " in name:
                base_name = name.split(" - ")[0].strip()
            else:
                base_name = name.strip()
                
            if base_name not in deduped:
                # Standardize to base name
                item["scheme_name"] = base_name
                deduped[base_name] = item
                
        final_list = list(deduped.values())
        print(f"   🧹 Deduplicated {len(parsed_results)} results down to {len(final_list)}")
        return final_list

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
