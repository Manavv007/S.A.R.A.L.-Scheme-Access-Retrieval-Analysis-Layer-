"""Unit tests for backend/app/models/scheme.py."""

from backend.app.models.scheme import (
    Scheme,
    content_hash,
    make_scheme_id,
    slugify,
    vector_id,
)


def test_slugify():
    assert slugify("Andhra Pradesh") == "andhra-pradesh"
    assert slugify("PM-KISAN!!") == "pm-kisan"
    assert slugify("") == ""


def test_make_scheme_id_stable():
    a = make_scheme_id("PM-KISAN", level="Central")
    b = make_scheme_id("PM-KISAN", level="Central")
    assert a == b == "central-pm-kisan"
    assert make_scheme_id("Farmer Aid", level="State", state="Gujarat") == "state-gujarat-farmer-aid"


def test_vector_id_deterministic_and_unique():
    sid = "central-pm-kisan"
    assert vector_id(sid, 0) == vector_id(sid, 0)       # deterministic
    assert vector_id(sid, 0) != vector_id(sid, 1)       # per-chunk unique
    assert vector_id("a", 0) != vector_id("b", 0)       # per-scheme unique


def test_content_hash_changes_with_content():
    assert content_hash("x") == content_hash("x")
    assert content_hash("x") != content_hash("y")


def test_scheme_new_and_metadata():
    s = Scheme.new("PM-KISAN", level="Central", target_occupation=["Farmer"],
                   income_limit=None, documents_required=["Aadhaar"])
    assert s.scheme_id == "central-pm-kisan"
    assert s.last_seen  # auto-filled
    meta = s.to_metadata()
    assert meta["scheme_id"] == "central-pm-kisan"
    assert meta["target_occupation"] == ["Farmer"]
    assert meta["documents_required"] == ["Aadhaar"]
    # None income_limit stripped from metadata
    assert "income_limit" not in meta


def test_compute_hash_changes_on_field_change():
    s1 = Scheme.new("X", benefits="A")
    s2 = Scheme.new("X", benefits="B")
    assert s1.compute_hash() != s2.compute_hash()
