"""Unit tests for backend/app/services/recommendation.py pure logic.

The service's __init__ loads heavy models, so we build a bare instance with
object.__new__ and inject fakes where needed.
"""

import pytest
from langchain_core.documents import Document

from backend.app.models.dtos import UserProfile
from backend.app.services.recommendation import RecommendationService


@pytest.fixture
def svc():
    return object.__new__(RecommendationService)


@pytest.fixture
def profile():
    return UserProfile(age=30, occupation="Farmer", state="Gujarat",
                       income="150000", caste="OBC", language="English")


def test_metadata_filter(svc, profile):
    f = svc._build_metadata_filter(profile)
    assert "$or" in f
    states = [c.get("state", {}).get("$eq") for c in f["$or"] if "state" in c]
    assert "Gujarat" in states
    assert any(c.get("level", {}).get("$eq") == "Central" for c in f["$or"])


@pytest.mark.parametrize("raw,first_name", [
    ('[{"scheme_name":"A","eligibility_status":"Eligible","reason":"r"}]', "A"),
    ('Here you go: [{"scheme_name":"B","eligibility_status":"Eligible","reason":"r"}] done', "B"),
])
def test_parse_response_array(svc, raw, first_name):
    out = svc._parse_response(raw)
    assert isinstance(out, list)
    assert out[0]["scheme_name"] == first_name


def test_extract_json_array_balanced(svc):
    text = 'noise [{"a":[1,2]},{"b":"]"}] trailing'
    extracted = svc._extract_json_array(text)
    assert extracted.startswith("[") and extracted.endswith("]")


@pytest.mark.parametrize("raw,expected", [
    ('{"verdict":"PASS","refined_query":""}', (True, "")),
    ('{"verdict":"FAIL","refined_query":"q"}', (False, "q")),
    ("not json", (True, "")),            # fail-open
])
def test_parse_critic(svc, raw, expected):
    assert svc._parse_critic(raw) == expected


def test_cosine(svc):
    assert abs(svc._cosine([1, 2, 3], [1, 2, 3]) - 1.0) < 1e-9
    assert abs(svc._cosine([1, 0], [0, 1])) < 1e-9
    assert svc._cosine([0, 0], [1, 1]) == 0.0


def test_is_state_match(svc):
    assert svc._is_state_match("Central", "Gujarat") is True
    assert svc._is_state_match("Gujarat", "Gujarat") is True
    assert svc._is_state_match("Kerala", "Gujarat") is False
    assert svc._is_state_match("", "Gujarat") is True  # untagged = open


def test_match_source(svc):
    idx = [
        {"name": "PM-KISAN", "apply_url": "u1", "source_url": "", "source_file": "", "documents_required": ["Aadhaar"]},
        {"name": "Gujarat Farmer Subsidy", "apply_url": "u2", "source_url": "", "source_file": "", "documents_required": []},
    ]
    assert svc._match_source("PM-KISAN", idx)["apply_url"] == "u1"
    assert svc._match_source("Gujarat Farmer Subsidy Scheme", idx)["apply_url"] == "u2"
    assert svc._match_source("Totally Unrelated", idx) == {}


class _FakeLLM:
    def generate_raw(self, prompt):
        return (
            '[{"scheme_name":"PM-KISAN","eligibility_status":"Eligible","reason":"ok"},'
            '{"scheme_name":"Kerala Aid","eligibility_status":"Near-Miss","reason":"Only in Kerala"}]'
        )


def test_generate_verdicts_grounding_and_status(svc, profile):
    svc.llm_engine = _FakeLLM()
    docs = [
        Document(page_content="PM-KISAN for farmers",
                 metadata={"name": "PM-KISAN", "apply_url": "https://pmkisan",
                           "documents_required": ["Aadhaar", "Land records"]}),
    ]
    out = svc._generate_verdicts(profile, docs)
    by = {o["scheme_name"]: o for o in out}

    assert by["PM-KISAN"]["eligibility_status"] == "Eligible"
    assert by["PM-KISAN"]["apply_url"] == "https://pmkisan"
    assert by["PM-KISAN"]["documents_required"] == ["Aadhaar", "Land records"]
    assert by["Kerala Aid"]["eligibility_status"] == "Near-Miss"


def test_generate_verdicts_empty(svc, profile):
    out = svc._generate_verdicts(profile, [])
    assert out[0]["scheme_name"] == "No Schemes Found"
    assert "documents_required" in out[0]
