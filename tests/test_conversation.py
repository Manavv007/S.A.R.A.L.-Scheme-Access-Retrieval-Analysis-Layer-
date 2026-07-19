"""Unit tests for the voice ConversationEngine slot-filling logic.

These build the engine via ``object.__new__`` and inject a fake LLM, so no
network / Groq calls happen. Eligibility + summary are stubbed.
"""

import json

import pytest

from backend.app.services.conversation import ConversationEngine, FIELDS


class _FakeLLM:
    """Returns a canned generate_raw payload; captures the last prompt."""

    def __init__(self, payload: str):
        self.payload = payload
        self.last_prompt = None

    def generate_raw(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.payload


def _engine(payload: str) -> ConversationEngine:
    eng = object.__new__(ConversationEngine)
    eng.llm = _FakeLLM(payload)
    return eng


def test_next_missing_order():
    eng = object.__new__(ConversationEngine)
    assert eng._next_missing({}) == "age"
    assert eng._next_missing({"age": 30}) == "occupation"
    full = {"age": 30, "occupation": "Farmer", "state": "Gujarat",
            "income": 100000, "caste": "OBC"}
    assert eng._next_missing(full) is None


def test_parse_json_object_tolerates_wrapping():
    eng = object.__new__(ConversationEngine)
    raw = 'Sure! {"profile_updates": {"age": 30}, "reply": "ok"} trailing'
    obj = eng._parse_json_object(raw)
    assert obj["profile_updates"]["age"] == 30
    assert eng._parse_json_object("not json") == {}


def test_collect_merges_updates_and_asks_next():
    payload = json.dumps({
        "profile_updates": {"occupation": "Farmer"},
        "reply": "Great! Which state do you live in?",
        "all_collected": False,
    })
    eng = _engine(payload)
    out = eng.converse(
        user_message="I am a farmer",
        profile={"age": 30},
        history=[],
        phase="collect",
        language="English",
    )
    assert out["profile"]["occupation"] == "Farmer"
    assert out["phase"] == "collect"
    assert out["done"] is False
    assert out["reply"]  # asks next question


def test_completion_triggers_recommend_and_summary(monkeypatch):
    # LLM extracts the final missing field (caste); once complete the engine
    # should call _recommend + _summarize and move to the qa phase.
    payload = json.dumps({
        "profile_updates": {"caste": "OBC"},
        "reply": "Thanks!",
        "all_collected": True,
    })
    eng = _engine(payload)

    fake_schemes = [{"scheme_name": "PM-KISAN", "eligibility_status": "Eligible",
                     "reason": "ok"}]
    monkeypatch.setattr(eng, "_recommend", lambda profile, language: fake_schemes)
    monkeypatch.setattr(eng, "_summarize", lambda schemes, language: "You qualify for PM-KISAN.")

    out = eng.converse(
        user_message="I am OBC",
        profile={"age": 30, "occupation": "Farmer", "state": "Gujarat", "income": 100000},
        history=[],
        phase="collect",
        language="English",
    )
    assert out["profile"]["caste"] == "OBC"
    assert out["phase"] == "qa"
    assert out["schemes"] == fake_schemes
    assert out["reply"] == "You qualify for PM-KISAN."


def test_qa_phase_routes_to_answer(monkeypatch):
    eng = object.__new__(ConversationEngine)
    monkeypatch.setattr(eng, "_answer",
                        lambda message, profile, history, language: "Here is how to apply.")
    out = eng.converse(
        user_message="How do I apply for PM-KISAN?",
        profile={"age": 30},
        history=[],
        phase="qa",
        language="English",
    )
    assert out["phase"] == "qa"
    assert out["reply"] == "Here is how to apply."


def test_fields_constant():
    assert FIELDS == ["age", "occupation", "state", "income", "caste"]
