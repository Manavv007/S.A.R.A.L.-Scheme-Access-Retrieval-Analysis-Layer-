"""
Recommendation service – matches user profiles against
government schemes using RAG retrieval + LLM analysis.

Pipeline (Phase 2):
    server-side Pinecone metadata filter  →  multi-vector retrieval
    →  Researcher-Critic relevance loop (a Critic LLM judges topic relevance
       and, on FAIL, proposes a refined query; retries up to 3×)
    →  candidate re-ranking (MiniLM similarity)
    →  LLM verdict generation, grounded with each scheme's source/apply URLs.
"""

import json
import math
import re

from backend.app.services.rag_retriever import RAGService
from backend.app.services.llm_engine import LLMEngine
from backend.app.models.dtos import UserProfile

# ── Phase 2 tuning knobs ─────────────────────────────────
MAX_RETRIEVAL_ATTEMPTS = 3      # Researcher-Critic retries
RERANK_TOP_N = 15               # docs kept after re-ranking for the verdict LLM
CANDIDATE_POOL = 40             # docs considered before re-ranking

# ── Critic prompt (relevance judge) ──────────────────────
_CRITIC_PROMPT = """\
You are a retrieval-quality Critic for a government-scheme recommender.

User: occupation="{occupation}", state="{state}".

Below are short snippets from the documents retrieved for this user:
{snippets}

Decide whether these documents are RELEVANT for finding government schemes
that match this user's occupation and state. Judge topic relevance only —
do NOT judge eligibility.

Respond with ONLY a JSON object, nothing else:
{{"verdict": "PASS" or "FAIL", "refined_query": "<a better search query if FAIL, else empty string>"}}"""


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
        Production-Grade Hybrid Retrieval Engine (Phase 2).

        Pipeline:
          server-side metadata filter  →  multi-vector retrieval
          →  Researcher-Critic relevance loop (retry up to 3×)
          →  candidate re-ranking  →  LLM verdicts (grounded with source URLs).
        """
        print(f"\n🚀 ENGINE START: {profile.occupation} | {profile.state} | {profile.income}")

        # Build the Pinecone metadata filter once (server-side pre-filtering).
        metadata_filter = self._build_metadata_filter(profile)
        print(f"   🧮 Server-side metadata filter: {metadata_filter}")

        refined_query = None
        valid_docs: list = []

        # ── Researcher-Critic loop ──
        for attempt in range(1, MAX_RETRIEVAL_ATTEMPTS + 1):
            print(f"\n🔁 RETRIEVAL ATTEMPT {attempt}/{MAX_RETRIEVAL_ATTEMPTS}"
                  + (f" (refined: '{refined_query}')" if refined_query else ""))

            raw_docs = self._retrieve_documents(profile, metadata_filter, refined_query)
            print(f"   📦 Aggregated {len(raw_docs)} raw documents.")

            # Thin client-side safety net (handles state-name normalization
            # edge cases that exact Pinecone $eq matching can miss).
            valid_docs = self._safety_filter(raw_docs, profile)
            print(f"   🎯 {len(valid_docs)}/{len(raw_docs)} docs passed the safety net.")

            passed, refined = self._critique(profile, valid_docs)
            if passed or attempt == MAX_RETRIEVAL_ATTEMPTS:
                print(f"   🧑‍⚖️ Critic verdict: {'PASS' if passed else 'STOP (max attempts)'}")
                break
            print(f"   🧑‍⚖️ Critic verdict: FAIL → refining query")
            refined_query = refined or None

        # ── Re-rank candidates before sending to the verdict LLM ──
        ranked_docs = self._rerank(profile, valid_docs)
        print(f"\n📝 GENERATING VERDICTS with top {len(ranked_docs)} re-ranked docs")
        return self._generate_verdicts(profile, ranked_docs)

    def _retrieve_documents(
        self,
        profile: UserProfile,
        metadata_filter: dict | None = None,
        refined_query: str | None = None,
    ) -> list:
        """
        Executes parallel retrieval strategies to maximize recall, applying
        the server-side metadata filter to every query.

        Strategy A: Semantic Search (Nuanced understanding)
        Strategy B: Metadata-Focused (State/Occupation keywords)
        Strategy C: Broad/National (Catch-all for central schemes)
        Strategy D: Critic's refined query (only when provided on a retry)
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

        print(f"🔍 [STRATEGY A] Semantic: '{query_a}'")
        print(f"🔍 [STRATEGY B] Keyword:  '{query_b}'")
        print(f"🔍 [STRATEGY C] National: '{query_c}'")

        docs_a = self.rag_service.get_raw_docs(query_a, k=10, filters=metadata_filter)
        docs_b = self.rag_service.get_raw_docs(query_b, k=10, filters=metadata_filter)
        docs_c = self.rag_service.get_raw_docs(query_c, k=15, filters=metadata_filter)
        all_docs = docs_a + docs_b + docs_c

        if refined_query:
            print(f"🔍 [STRATEGY D] Refined: '{refined_query}'")
            docs_d = self.rag_service.get_raw_docs(refined_query, k=15, filters=metadata_filter)
            all_docs += docs_d

        print(f"   Found: A={len(docs_a)}, B={len(docs_b)}, C={len(docs_c)}"
              + (f", D={len(all_docs) - len(docs_a) - len(docs_b) - len(docs_c)}" if refined_query else ""))

        # Merge & Deduplicate by content signature
        unique_docs = []
        seen_content = set()
        for doc in all_docs:
            sig = doc.page_content[:200].strip()
            if sig not in seen_content:
                unique_docs.append(doc)
                seen_content.add(sig)

        return unique_docs

    # ── Server-side metadata filter ──────────────────────

    def _build_metadata_filter(self, profile: UserProfile) -> dict:
        """
        Build a Pinecone metadata filter that keeps Central/national schemes
        plus the user's own state, pushing this work server-side instead of
        post-filtering in Python.

        Backward-compatible with three data vintages:
          • old PDF vectors tagged only with state="Central"/"<State>"
          • new PDF vectors with level + state
          • scraped vectors with level (+ state for State schemes)
        """
        return {
            "$or": [
                {"level": {"$eq": "Central"}},
                {"state": {"$eq": "Central"}},
                {"state": {"$eq": profile.state}},
            ]
        }

    def _safety_filter(self, docs: list, profile: UserProfile) -> list:
        """
        Thin client-side safety net applied **after** the server-side Pinecone
        metadata filter. Server-side filtering does the heavy lifting; this only
        catches state-name normalization edge cases that exact ``$eq`` matching
        can miss (e.g. "Jammu & Kashmir" vs "Jammu and Kashmir") and drops
        anything that slipped through.
        """
        kept = []
        for doc in docs:
            raw_state = doc.metadata.get("state", "central")
            if self._is_state_match(raw_state, profile.state):
                kept.append(doc)
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

    # ── Researcher-Critic relevance judge ────────────────

    def _critique(self, profile: UserProfile, docs: list) -> tuple[bool, str]:
        """
        Ask a Critic LLM whether the retrieved docs are topically relevant to
        the user's occupation/state. Returns (passed, refined_query).

        Fails open: if no docs, returns FAIL with a refined query; if the LLM
        response can't be parsed, returns PASS (don't block the pipeline).
        """
        if not docs:
            return (False, f"government welfare schemes for {profile.occupation} in {profile.state}")

        snippets = "\n".join(
            f"- {d.page_content[:160].strip()}" for d in docs[:8]
        )
        prompt = _CRITIC_PROMPT.format(
            occupation=profile.occupation,
            state=profile.state,
            snippets=snippets,
        )
        try:
            raw = self.llm_engine.generate_raw(prompt)
        except Exception as e:
            print(f"   ⚠️ Critic call failed ({e}); assuming PASS")
            return (True, "")

        verdict, refined = self._parse_critic(raw)
        return (verdict, refined)

    @staticmethod
    def _parse_critic(raw: str) -> tuple[bool, str]:
        """Parse the Critic's JSON. Defaults to PASS on parse failure."""
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                obj = json.loads(raw[start:end + 1])
                verdict = str(obj.get("verdict", "PASS")).strip().upper() == "PASS"
                return (verdict, str(obj.get("refined_query", "")).strip())
        except (json.JSONDecodeError, ValueError):
            pass
        return (True, "")

    # ── Candidate re-ranking ─────────────────────────────

    def _rerank(self, profile: UserProfile, docs: list) -> list:
        """
        Re-rank candidate docs by similarity to a profile query, then keep the
        top-N for the verdict LLM. Reuses the already-loaded MiniLM embeddings
        (no extra model download), so this is cheap and dependency-free.
        """
        if not docs:
            return docs
        pool = docs[:CANDIDATE_POOL]

        query = (
            f"Government schemes for a {profile.occupation} in {profile.state}, "
            f"annual income {profile.income}, category {profile.caste}."
        )
        try:
            embeddings = self.rag_service.embeddings
            q_vec = embeddings.embed_query(query)
            d_vecs = embeddings.embed_documents([d.page_content[:1000] for d in pool])
        except Exception as e:
            print(f"   ⚠️ Re-rank embedding failed ({e}); keeping original order")
            return pool[:RERANK_TOP_N]

        scored = sorted(
            zip(pool, d_vecs),
            key=lambda pair: self._cosine(q_vec, pair[1]),
            reverse=True,
        )
        ranked = [doc for doc, _ in scored][:RERANK_TOP_N]
        print(f"   📊 Re-ranked {len(pool)} candidates → kept {len(ranked)}")
        return ranked

    @staticmethod
    def _cosine(a: list, b: list) -> float:
        """Cosine similarity between two equal-length vectors (pure Python)."""
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    # ── Verdict grounding ────────────────────────────────

    @staticmethod
    def _build_source_index(docs: list) -> list[dict]:
        """
        Collect source metadata (name + apply_url/source_url/source_file) from
        the docs so verdicts can be grounded back to their origin.
        """
        index = []
        seen = set()
        for d in docs:
            m = d.metadata or {}
            name = (m.get("name") or m.get("source_file") or "").strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            index.append({
                "name": name,
                "apply_url": m.get("apply_url", "") or "",
                "source_url": m.get("source_url", "") or "",
                "source_file": m.get("source_file", "") or "",
            })
        return index

    @staticmethod
    def _match_source(scheme_name: str, source_index: list[dict]) -> dict:
        """Best-effort match of an LLM scheme name to a source metadata entry."""
        if not scheme_name:
            return {}
        target = scheme_name.lower().strip()
        # 1) exact, 2) bidirectional substring on a few significant tokens
        for entry in source_index:
            if entry["name"].lower().strip() == target:
                return entry
        for entry in source_index:
            ename = entry["name"].lower()
            if target in ename or ename in target:
                return entry
        target_tokens = {t for t in re.split(r"\W+", target) if len(t) > 3}
        for entry in source_index:
            etokens = {t for t in re.split(r"\W+", entry["name"].lower()) if len(t) > 3}
            if target_tokens and len(target_tokens & etokens) >= 2:
                return entry
        return {}

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
                "apply_url": "",
                "source_url": "",
                "source": "",
            }]

        # Prioritize docs: shorter content usually headers/summaries
        # But here we just take top N to avoid token overflow
        top_docs = docs[:15] 
        context = "\n\n".join(doc.page_content for doc in top_docs)

        # Source metadata for grounding each verdict back to its origin.
        source_index = self._build_source_index(top_docs)

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

        # Ground each verdict: attach origin URLs from the retrieved metadata.
        for item in final_list:
            match = self._match_source(item.get("scheme_name", ""), source_index)
            item["apply_url"] = match.get("apply_url", "")
            item["source_url"] = match.get("source_url", "")
            item["source"] = match.get("source_file", "")

        grounded = sum(1 for i in final_list if i.get("apply_url") or i.get("source_url") or i.get("source"))
        print(f"   🧹 Deduplicated {len(parsed_results)} results down to {len(final_list)} "
              f"({grounded} grounded with a source)")
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
