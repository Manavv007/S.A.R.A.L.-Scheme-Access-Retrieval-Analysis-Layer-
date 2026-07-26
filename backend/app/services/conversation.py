"""
Conversation engine for the live "talk to an officer" voice mode.

A slot-filling dialogue manager that collects a citizen's demographic profile
one detail at a time, in their own language, then hands off to the existing
eligibility engine and speaks the matching schemes. Follow-up questions are
answered via the existing RAG chat pipeline.

Design notes:
* Phase transitions are decided in **code** (deterministic), not by the LLM.
  The LLM only extracts slot values and phrases the next reply.
* One combined LLM call per collect-turn (extract + reply) to keep latency and
  free-tier usage low.
* The heavy recommendation service is fetched lazily, so STT/TTS-only traffic
  never loads the embedding model.
"""

import json
import re

from backend.app.models.dtos import UserProfile
from backend.app.services.providers import get_llm_engine
from backend.app.core.logging_config import get_logger

logger = get_logger("conversation")

# Canonical option lists (mirror web/src/lib/constants.ts).
OCCUPATIONS = [
    "Farmer", "Student", "Business", "Salaried", "Self-Employed",
    "Unemployed", "Retired", "Other",
]
CATEGORIES = ["General", "OBC", "SC", "ST", "EWS", "Other"]
STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Jammu & Kashmir", "Ladakh",
]

# Order in which demographic details are collected.
FIELDS = ["age", "occupation", "state", "income", "caste"]

_FIELD_LABEL = {
    "age": "age",
    "occupation": "occupation",
    "state": "state of residence",
    "income": "annual household income (in rupees)",
    "caste": "social category (General / OBC / SC / ST / EWS)",
}

_TURN_PROMPT = """\
You are a warm, respectful Government Scheme Officer helping an Indian citizen.
Speak ONLY in {language}. Be friendly, patient and concise.

You are collecting the citizen's details, one at a time, to find welfare
schemes they are eligible for. The details you need (with allowed values):
- age: a number
- occupation: one of {occupations}
- state: one of {states}
- income: annual household income in rupees (a number)
- caste: one of {categories}

Already collected (JSON): {collected}
Recent conversation:
{history}

The citizen just said: "{message}"

Do TWO things:
1. Extract any of the above details from what they said. Normalize each to the
   ALLOWED values (pick the closest match; use null if not stated or unclear).
2. Write your next reply in {language}: warmly acknowledge what they said and
   ask for the NEXT missing detail (only one question). If every detail is
   already known, briefly say you will now look up their schemes.

Respond with ONLY a JSON object, nothing else:
{{"profile_updates": {{"age": <int|null>, "occupation": <str|null>, "state": <str|null>, "income": <int|null>, "caste": <str|null>}}, "reply": "<your reply in {language}>", "all_collected": <true|false>}}"""

_OPENING_PROMPT = """\
You are a warm, respectful Government Scheme Officer helping an Indian citizen.
Speak ONLY in {language}. In 1-2 friendly sentences, greet the citizen, briefly
say you'll ask a few quick questions to find government schemes they qualify
for, and then ask for their {field}. Output ONLY the spoken reply text."""

_SEEDED_OPENING_PROMPT = """\
You are a warm, respectful Government Scheme Officer helping an Indian citizen.
Speak ONLY in {language}. In 1-2 friendly spoken sentences: greet them and
invite them to ask about government schemes or eligibility. Do NOT mention
their profile details, occupation, state, income, or category. Do NOT list
schemes or say you will look them up now. Output ONLY the spoken reply text."""

_SUMMARY_PROMPT = """\
You are a warm, respectful Government Scheme Officer speaking to a citizen.
Speak ONLY in {language}. Based on the analysis below, tell the citizen which
schemes they are ELIGIBLE for and give a one-line reason for each. If there are
NEAR-MISS schemes, briefly mention them and the single blocker. Keep it natural
and spoken (this will be read aloud), concise, and end by inviting them to ask
follow-up questions about any scheme.

Analysis (JSON): {schemes}

Output ONLY the spoken reply text in {language}."""


class ConversationEngine:
    """Slot-filling voice dialogue manager over the eligibility + chat engines."""

    def __init__(self) -> None:
        # ChatGroq is light to construct; the recommendation service (which
        # loads the embedding model) is fetched lazily only when needed.
        self.llm = get_llm_engine()

    # ── Public entry point ───────────────────────────────

    def converse(
        self,
        *,
        user_message: str = "",
        profile: dict | None = None,
        history: list | None = None,
        phase: str = "greet",
        language: str = "English",
    ) -> dict:
        profile = {k: v for k, v in (profile or {}).items() if v not in (None, "")}
        history = history or []
        language = language or "English"
        user_message = (user_message or "").strip()

        # ── Opening turn ──
        if phase in (None, "", "greet") and not user_message:
            missing = self._next_missing(profile)
            # Form already supplied every demographic slot → skip collection.
            # Greet briefly only; keep profile for later Q&A (no scheme dump).
            if profile and missing is None:
                reply = self._seeded_opening(language, profile)
                return {
                    "reply": reply, "profile": profile,
                    "phase": "qa", "done": False, "schemes": [],
                }
            # Partial seed → ask only the next missing field.
            # Empty profile → classic collect-from-age flow.
            reply = self._opening(language, missing or "age")
            return {
                "reply": reply, "profile": profile,
                "phase": "collect", "done": False, "schemes": [],
            }

        # ── Q&A phase: free-form follow-ups about schemes ──
        if phase == "qa":
            reply = self._answer(user_message, profile, history, language)
            return {
                "reply": reply, "profile": profile,
                "phase": "qa", "done": False, "schemes": [],
            }

        # ── Collect phase: extract slots + ask the next one ──
        updates, reply = self._turn(user_message, profile, history, language)
        for key, val in updates.items():
            if key in FIELDS and val not in (None, ""):
                profile[key] = val

        if self._next_missing(profile):
            return {
                "reply": reply, "profile": profile,
                "phase": "collect", "done": False, "schemes": [],
            }

        # ── All details collected → run eligibility + speak results ──
        schemes = self._recommend(profile, language)
        summary = self._summarize(schemes, language)
        return {
            "reply": summary, "profile": profile,
            "phase": "qa", "done": False, "schemes": schemes,
        }

    # ── Slot tracking ────────────────────────────────────

    @staticmethod
    def _next_missing(profile: dict) -> str | None:
        for field in FIELDS:
            val = profile.get(field)
            if val in (None, ""):
                return field
        return None

    # ── LLM turns ────────────────────────────────────────

    def _turn(
        self, message: str, profile: dict, history: list, language: str
    ) -> tuple[dict, str]:
        """One combined extract-and-reply LLM call. Returns (updates, reply)."""
        prompt = _TURN_PROMPT.format(
            language=language,
            occupations=", ".join(OCCUPATIONS),
            states=", ".join(STATES),
            categories=", ".join(CATEGORIES),
            collected=json.dumps(profile, ensure_ascii=False),
            history=self._format_history(history),
            message=message,
        )
        try:
            raw = self.llm.generate_raw(prompt)
        except Exception as e:  # pragma: no cover - network dependent
            logger.warning(f"turn LLM failed ({e})")
            return ({}, "Sorry, could you please repeat that?")

        obj = self._parse_json_object(raw)
        if not obj:
            return ({}, "Sorry, I didn't catch that. Could you say it again?")

        updates = obj.get("profile_updates") or {}
        if not isinstance(updates, dict):
            updates = {}
        reply = str(obj.get("reply") or "").strip() or "Could you tell me a bit more?"
        return (updates, reply)

    def _opening(self, language: str, first_field: str) -> str:
        prompt = _OPENING_PROMPT.format(
            language=language, field=_FIELD_LABEL.get(first_field, first_field)
        )
        try:
            return self.llm.generate_raw(prompt).strip()
        except Exception as e:  # pragma: no cover - network dependent
            logger.warning(f"opening LLM failed ({e})")
            return "Hello! I'll ask you a few quick questions to find schemes you qualify for. First, what is your age?"

    def _seeded_opening(self, language: str, _profile: dict) -> str:
        prompt = _SEEDED_OPENING_PROMPT.format(language=language)
        try:
            return self.llm.generate_raw(prompt).strip()
        except Exception as e:  # pragma: no cover - network dependent
            logger.warning(f"seeded opening LLM failed ({e})")
            return "Namaste. How can I help you with government schemes today?"

    def _summarize(self, schemes: list, language: str) -> str:
        prompt = _SUMMARY_PROMPT.format(
            language=language,
            schemes=json.dumps(schemes, ensure_ascii=False),
        )
        try:
            return self.llm.generate_raw(prompt).strip()
        except Exception as e:  # pragma: no cover - network dependent
            logger.warning(f"summary LLM failed ({e})")
            n = sum(1 for s in schemes if str(s.get("eligibility_status", "")).lower() == "eligible")
            return f"I found {n} scheme(s) you may be eligible for. Please ask me about any of them."

    def _answer(self, message: str, profile: dict, history: list, language: str) -> str:
        """Answer a follow-up via profile-grounded fusion.

        A deterministic eligibility pre-check (state/category mismatch) answers
        first when it can. Otherwise we retrieve scheme docs only when they look
        useful, then let the fused prompt reason over the form + docs together.
        There is no profile-or-RAG either/or branch, so an empty retrieval can
        never make the bot claim it "lacks information".
        """
        from backend.app.services.providers import get_rag_service, get_llm_engine

        llm = get_llm_engine()
        intent = llm.classify_intent(message, profile=profile, history=history)
        context = ""
        if intent in ("schemes", "both"):
            context = get_rag_service().get_context(message, k=5)
        return llm.generate_answer(
            message,
            context=context,
            language=language,
            history=history,
            profile=profile,
            intent=intent,
        )

    # ── Eligibility hand-off ─────────────────────────────

    def _recommend(self, profile: dict, language: str) -> list:
        from backend.app.services.providers import get_recommendation_service

        age_digits = re.sub(r"[^0-9]", "", str(profile.get("age", "")))
        up = UserProfile(
            age=int(age_digits or 0),
            occupation=str(profile.get("occupation") or "Other"),
            state=str(profile.get("state") or ""),
            income=str(profile.get("income") or "0"),
            caste=str(profile.get("caste") or "General"),
            language=language,
        )
        return get_recommendation_service().get_eligible_schemes(up)

    # ── Helpers ──────────────────────────────────────────

    @staticmethod
    def _format_history(history: list) -> str:
        if not history:
            return "(none)"
        turns = []
        for msg in history[-8:]:
            role = "Citizen" if msg.get("role") == "user" else "Officer"
            turns.append(f"{role}: {msg.get('content', '')}")
        return "\n".join(turns)

    @staticmethod
    def _parse_json_object(raw: str) -> dict:
        """Extract the first balanced JSON object from LLM output."""
        if not raw:
            return {}
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end < start:
            return {}
        try:
            obj = json.loads(raw[start:end + 1])
            return obj if isinstance(obj, dict) else {}
        except (json.JSONDecodeError, ValueError):
            return {}
