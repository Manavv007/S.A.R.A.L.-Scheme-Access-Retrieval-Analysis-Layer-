"""
LLM engine service – sends user queries (+ profile + optional RAG context) to Groq.

Architecture: profile-grounded fusion (no binary router).
  The citizen form is ALWAYS injected as hard context (Source A). Scheme
  documents (Source B) are retrieved in parallel and injected when relevant.
  The model SYNTHESISES both -- it never has to "choose a path", which removes
  the previous failure where a RAG-or-profile branch gave up on empty retrieval.

  A deterministic pre-check (backend.app.services.eligibility) answers
  profile-settled questions (e.g. state/category mismatch) before the LLM runs,
  so those replies are auditable and free.
"""

from __future__ import annotations

import json
import logging
from typing import Literal, Iterator

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.app.core.config import settings
from backend.app.services.eligibility import scope_hint

logger = logging.getLogger("saral.llm")

# Kept for callers/type-hints that still pass an intent; the engine ignores the
# routing and always fuses profile + context.
Intent = Literal["profile_only", "schemes", "both"]

# Intent classifier is retained only as a cheap signal for *whether to retrieve
# scheme docs* (RAG). It never gates the answer path. A "profile_only" verdict
# simply skips the (slow) retrieval call -- the profile is always shown.
_CLASSIFY_PROMPT = """\
You route questions for an Indian government-scheme assistant.

Citizen form on file (JSON; may be empty):
{profile_json}

Recent conversation (may be empty):
{history}

Latest user question:
{query}

Decide whether SCHEME DOCUMENTS are needed to answer well.
- "profile_only": The question is only about THIS citizen's own submitted
  details (age, occupation, state, income, caste/category, language). Scheme
  documents are not needed.
- "schemes": The question is about schemes, eligibility rules, documents,
  application process, benefits, or general scheme knowledge. Scheme documents
  ARE useful.
- "both": The question needs the citizen's form facts AND scheme documents.

Respond with ONLY a JSON object, no other text:
{{"intent":"profile_only"}}
or {{"intent":"schemes"}}
or {{"intent":"both"}}
"""

# Single fused template. The citizen form is ALWAYS present as hard context.
# The model may reason eligibility from the form + general knowledge; it is
# only allowed to say "I don't have scheme information" when BOTH the form
# lacks the needed personal detail AND retrieval returned nothing.
_FUSED_TEMPLATE = """\
System: You are an expert Government Scheme Advisor for India.
Keep the answer concise, warm, and helpful.
{language_instruction}

You always have TWO sources. Use BOTH to answer:

Source A -- Citizen form (GROUND TRUTH about THIS user):
{citizen_profile}

Source B -- Retrieved scheme documents (rules about schemes, NOT the user's facts):
{context}

Verified scope facts (these are confirmed; prefer them over guessing):
{scope_hint}

Rules for combining them:
1. The citizen form describes THIS user. Never confuse a scheme's income/age
   limits in Source B with the citizen's own figures in Source A.
2. For eligibility questions (e.g. "why am I not eligible for X?", "can I apply
   for X?"), reason from Source A + the verified scope fact. For example, if the
   verified fact says a scheme is limited to a state and Source A shows the
   citizen is in a different state, explain that mismatch in plain, natural
   language -- do NOT read out a robotic template, and do NOT claim you lack
   information. You may also use general knowledge of how Indian schemes are
   scoped (e.g. reserved categories) when the form shows a mismatch.
3. Use Source B for scheme specifics: subsidy %, documents, deadlines, how to
   apply, exact criteria. Use Source A only to personalize. Feel free to
   discuss ANY scheme the user mentions using your general knowledge; a missing
   Source B document is not a reason to refuse to help.
4. Only say "I don't have enough information about that scheme" if BOTH the form
   lacks the needed personal detail AND Source B returned no relevant document
   AND there is no verified scope fact. If the form or a verified fact already
   answers the question, answer from it and do not claim missing data.
5. Speak naturally and helpfully in the user's chosen language. This is a
   helpful assistant, not a fixed-questionnaire bot.

User: {query}

Answer:"""


def _format_income(val) -> str:
    raw = str(val).strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits:
        try:
            return f"₹{int(digits):,} per year (annual household income)"
        except ValueError:
            pass
    return raw


def format_citizen_profile(profile: dict | None) -> str:
    """Human-readable form profile for prompts."""
    if not profile:
        return (
            "(No eligibility form on file yet. If the user asks what they "
            "submitted, say they have not filled the form.)"
        )
    lines = []
    order = [
        ("age", "Age"),
        ("occupation", "Occupation"),
        ("state", "State"),
        ("income", "Annual household income"),
        ("caste", "Social category"),
        ("language", "Preferred language"),
    ]
    for key, label in order:
        val = profile.get(key)
        if val in (None, ""):
            continue
        if key == "income":
            lines.append(f"- {label}: {_format_income(val)}")
        else:
            lines.append(f"- {label}: {val}")
    return "\n".join(lines) if lines else "(empty profile)"


def _parse_intent(raw: str) -> Intent:
    text = (raw or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            obj = json.loads(text[start : end + 1])
            intent = str(obj.get("intent", "")).strip().lower()
            if intent in ("profile_only", "schemes", "both"):
                return intent  # type: ignore[return-value]
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    lowered = text.lower()
    if "profile_only" in lowered:
        return "profile_only"
    if "both" in lowered:
        return "both"
    return "schemes"


class LLMEngine:
    """Groq Llama-3 engine with profile-grounded fused answering."""

    def __init__(self) -> None:
        self.llm = ChatGroq(
            temperature=0.0,
            model_name="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
        )
        self.parser = StrOutputParser()
        self.fused_prompt = PromptTemplate(
            input_variables=[
                "query",
                "language_instruction",
                "citizen_profile",
                "context",
                "scope_hint",
            ],
            template=_FUSED_TEMPLATE,
        )
        self.fused_chain = self.fused_prompt | self.llm | self.parser

    def _lang_instruction(self, language: str) -> str:
        if language and language != "English":
            return (
                f"\nAnswer the user's question in {language}. "
                f"Keep technical terms (like scheme names) in English if needed, "
                f"but explain in {language}."
            )
        return ""

    def _format_history(self, history: list | None) -> str:
        if not history:
            return "(none)"
        turns = []
        for msg in history[-6:]:
            role = "User" if msg.get("role") == "user" else "AI"
            turns.append(f"{role}: {msg.get('content', '')}")
        return "\n".join(turns) if turns else "(none)"

    def _history_query(self, query: str, history: list | None) -> str:
        if not history:
            return query
        turns = []
        for msg in history[-10:]:
            role = "User" if msg.get("role") == "user" else "AI"
            turns.append(f"{role}: {msg.get('content', '')}")
        if not turns:
            return query
        return (
            "Previous conversation:\n"
            + "\n".join(turns)
            + "\n\nLatest question:\n"
            + query
        )

    def classify_intent(
        self,
        query: str,
        profile: dict | None = None,
        history: list | None = None,
    ) -> Intent:
        """LLM router: profile_only | schemes | both.

        Used ONLY to decide whether to spend a retrieval call. The answer path
        is always fused (see generate_answer / generate_answer_stream).
        """
        prompt = _CLASSIFY_PROMPT.format(
            profile_json=json.dumps(profile or {}, ensure_ascii=False),
            history=self._format_history(history),
            query=(query or "").strip(),
        )
        try:
            raw = self.parser.invoke(self.llm.invoke(prompt))
            intent = _parse_intent(raw)
            logger.info("chat_intent=%s query=%r", intent, (query or "")[:80])
            return intent
        except Exception as e:  # pragma: no cover - network dependent
            logger.warning("intent classify failed (%s); defaulting to schemes", e)
            return "schemes"

    def generate_raw(self, prompt: str) -> str:
        """Send a fully-formed prompt directly to the LLM (no template)."""
        response = self.llm.invoke(prompt)
        return self.parser.invoke(response)

    def _scope_hint(self, query: str, profile: dict | None) -> str:
        """Build the verified-scope hint block (never a hardcoded verdict).

        Returns a short, scheme-only fact string for injection into the prompt,
        or a placeholder when no registered scheme is precisely mentioned. The
        LLM is responsible for answering naturally from this hint + the form.
        """
        try:
            fact = scope_hint(profile, query)
        except Exception as e:  # safety net: a hint failure must never break a turn
            logger.warning("scope_hint failed (%s); continuing without hint", e)
            fact = None
        return fact or "(no verified scope facts for this query)"

    def generate_answer(
        self,
        query: str,
        context: str = "",
        language: str = "English",
        history: list | None = None,
        profile: dict | None = None,
        intent: Intent | None = None,
    ) -> str:
        """Answer via the fused profile+context template.

        A verified-scope hint is computed and injected as a prompt fact; the LLM
        answers naturally (in the user's language) rather than reading a
        hardcoded verdict. There is no binary router, so empty retrieval cannot
        make the bot claim it lacks information.
        """
        full_query = self._history_query(query, history)
        citizen = format_citizen_profile(profile)
        lang = self._lang_instruction(language)
        hint = self._scope_hint(query, profile)
        return self.fused_chain.invoke({
            "query": full_query,
            "language_instruction": lang,
            "citizen_profile": citizen,
            "context": (context or "").strip() or "(no scheme documents retrieved)",
            "scope_hint": hint,
        })

    def generate_answer_stream(
        self,
        query: str,
        context: str = "",
        language: str = "English",
        history: list | None = None,
        profile: dict | None = None,
        intent: Intent | None = None,
    ) -> Iterator[str]:
        """Stream the fused answer token-by-token.

        A verified-scope hint is injected like in generate_answer; the LLM
        produces the natural-language reply (no hardcoded short-circuit).
        """
        full_query = self._history_query(query, history)
        citizen = format_citizen_profile(profile)
        lang = self._lang_instruction(language)
        hint = self._scope_hint(query, profile)
        prompt_value = self.fused_prompt.format(
            query=full_query,
            language_instruction=lang,
            citizen_profile=citizen,
            context=(context or "").strip() or "(no scheme documents retrieved)",
            scope_hint=hint,
        )
        for chunk in self.llm.stream(prompt_value):
            text = getattr(chunk, "content", None)
            if text is None:
                text = str(chunk)
            if text:
                yield text
