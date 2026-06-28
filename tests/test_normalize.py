"""Unit tests for scraper/saral_scraper/normalize.py."""

import pytest

from saral_scraper import normalize as nz


@pytest.mark.parametrize("text,expected", [
    ("2.5 lakh", 250000),
    ("Rs. 8,00,000 per annum", 800000),
    ("1 crore", 10000000),
    ("250000", 250000),
    ("no income limit", None),
    ("not applicable", None),
    ("", None),
    (None, None),
])
def test_parse_income(text, expected):
    assert nz.parse_income(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("Age 18 to 40 years", (18, 40)),
    ("applicants above 60", (60, None)),
    ("children up to 21 years", (None, 21)),
    ("40 - 18", (18, 40)),          # reversed range normalized
    ("no age info", (None, None)),
    ("", (None, None)),
])
def test_parse_age_range(text, expected):
    assert nz.parse_age_range(text) == expected


def test_detect_occupations():
    found = nz.detect_occupations("Scholarship for students and farmers in agriculture")
    assert "Student" in found
    assert "Farmer" in found
    assert nz.detect_occupations("") == []


def test_detect_caste_eligibility():
    found = nz.detect_caste_eligibility("Open to SC and ST and OBC candidates")
    assert set(["SC", "ST", "OBC"]).issubset(set(found))


def test_clean_text():
    assert nz.clean_text("  <b>Hello</b>&amp;  world  ") == "Hello& world"
    assert nz.clean_text(None) == ""


def test_to_list():
    assert nz.to_list("Aadhaar; Income certificate, Caste cert") == [
        "Aadhaar", "Income certificate", "Caste cert",
    ]
    assert nz.to_list(["a", "", "  b  "]) == ["a", "b"]
    assert nz.to_list(None) == []
