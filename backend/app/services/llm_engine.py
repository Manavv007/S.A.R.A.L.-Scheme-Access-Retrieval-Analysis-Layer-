"""
LLM engine service – sends user queries (+ optional RAG context) to Groq.

Intent routing:
  profile_only → answer from the citizen form only (no Pinecone)
  schemes/both → retrieve scheme docs, then answer with form + docs
"""

from __future__ import annotations

import json
import logging
from typing import Literal

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.app.core.config import settings

logger = logging.getLogger("saral.llm")

Intent = Literal["profile_only", "schemes", "both"]

_CLASSIFY_PROMPT = """\
You route questions for an Indian government-scheme assistant.

Citizen form on file (JSON; may be empty):
{profile_json}

Recent conversation (may be empty):
{history}

Latest user question:
{query}

Choose exactly ONE intent:
- "profile_only": The question is only about THIS citizen's own submitted details
  (age, occupation, state, income, caste/category, language, what they filled
  in the form). Scheme documents are NOT needed.
- "schemes": The question is about schemes, eligibility rules, documents,
  application process, benefits, or general scheme knowledge. Scheme documents
  ARE needed. The form may help personalize but is not the main answer source.
- "both": The question needs the citizen's form facts AND scheme documents
  (e.g. "given my income, am I eligible for X?").

Respond with ONLY a JSON object, no other text:
{{"intent":"profile_only"}}
or {{"intent":"schemes"}}
or {{"intent":"both"}}
"""

_PROFILE_ONLY_TEMPLATE = """\
System: You are an expert Government Scheme Advisor for India.
Keep the answer concise and helpful.
{language_instruction}

You are answering using ONLY the citizen's eligibility form below.
This form is ground truth about the user. Scheme documents are intentionally
NOT provided — do not invent scheme rules and do not say you lack the user's
form details if they appear below.

Citizen form:
{citizen_profile}

User: {query}

Answer:"""

_RAG_TEMPLATE = """\
System: You are an expert Government Scheme Advisor for India.
Keep the answer concise and helpful.
{language_instruction}

You have two sources:

Source A — Citizen form (GROUND TRUTH about THIS user):
{citizen_profile}

Source B — Retrieved scheme documents (rules about schemes, NOT the user's facts):
{context}

Rules:
1. Questions about the citizen's own submitted details (age, occupation, state,
   income, caste, what they stated on the form) → answer from Source A only.
   Never confuse Source B income/eligibility limits with the citizen's income.
2. Questions about schemes, eligibility rules, documents, how to apply → use
   Source B. Use Source A only to personalize.
3. If Source B lacks a scheme fact, say you don't have enough information in
   the documents. If Source A lacks a personal detail, say it was not on the form.

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
    """Groq Llama-3 engine with intent-based RAG routing."""

    def __init__(self) -> None:
        self.llm = ChatGroq(
            temperature=0.0,
            model_name="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
        )
        self.parser = StrOutputParser()
        self.profile_prompt = PromptTemplate(
            input_variables=["query", "language_instruction", "citizen_profile"],
            template=_PROFILE_ONLY_TEMPLATE,
        )
        self.rag_prompt = PromptTemplate(
            input_variables=[
                "query",
                "language_instruction",
                "citizen_profile",
                "context",
            ],
            template=_RAG_TEMPLATE,
        )
        self.profile_chain = self.profile_prompt | self.llm | self.parser
        self.rag_chain = self.rag_prompt | self.llm | self.parser

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
        """LLM router: profile_only | schemes | both."""
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

    def generate_answer(
        self,
        query: str,
        context: str = "",
        language: str = "English",
        history: list | None = None,
        profile: dict | None = None,
        intent: Intent | None = None,
    ) -> str:
        """Answer using profile-only or RAG template based on intent."""
        resolved = intent or ("profile_only" if not (context or "").strip() else "schemes")
        full_query = self._history_query(query, history)
        citizen = format_citizen_profile(profile)
        lang = self._lang_instruction(language)

        if resolved == "profile_only":
            return self.profile_chain.invoke({
                "query": full_query,
                "language_instruction": lang,
                "citizen_profile": citizen,
            })

        return self.rag_chain.invoke({
            "query": full_query,
            "language_instruction": lang,
            "citizen_profile": citizen,
            "context": (context or "").strip() or "(no scheme documents retrieved)",
        })

    def generate_answer_stream(
        self,
        query: str,
        context: str = "",
        language: str = "English",
        history: list | None = None,
        profile: dict | None = None,
        intent: Intent | None = None,
    ):
        """Stream the answer token-by-token."""
        resolved = intent or ("profile_only" if not (context or "").strip() else "schemes")
        full_query = self._history_query(query, history)
        citizen = format_citizen_profile(profile)
        lang = self._lang_instruction(language)

        if resolved == "profile_only":
            prompt_value = self.profile_prompt.format(
                query=full_query,
                language_instruction=lang,
                citizen_profile=citizen,
            )
        else:
            prompt_value = self.rag_prompt.format(
                query=full_query,
                language_instruction=lang,
                citizen_profile=citizen,
                context=(context or "").strip() or "(no scheme documents retrieved)",
            )

        for chunk in self.llm.stream(prompt_value):
            text = getattr(chunk, "content", None)
            if text is None:
                text = str(chunk)
            if text:
                yield text
