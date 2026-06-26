"""
Normalization helpers for the scraper pipelines.

Pure functions (no Scrapy/IO dependencies) so they're trivially unit-testable
in Phase 5. They turn messy portal text into the typed values the canonical
Scheme schema expects.
"""

from __future__ import annotations

import re
from typing import Optional

from w3lib.html import remove_tags, replace_entities

# ── Text cleaning ───────────────────────────────────────────────────────────

_WS_RE = re.compile(r"\s+")


def clean_text(value: Optional[str]) -> str:
    """Strip HTML tags/entities and collapse whitespace."""
    if not value:
        return ""
    text = remove_tags(replace_entities(str(value)))
    return _WS_RE.sub(" ", text).strip()


def to_list(value) -> list[str]:
    """Coerce a value (str with separators, or list) into a clean list[str]."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        # split on common separators: newline, semicolon, bullet, comma
        items = re.split(r"[\n;•·,]+", str(value))
    out = []
    for it in items:
        c = clean_text(it)
        if c:
            out.append(c)
    return out


# ── Income parsing ──────────────────────────────────────────────────────────

_NUM_RE = re.compile(r"(\d+(?:[.,]\d+)*)")


def _to_number(token: str) -> Optional[float]:
    token = token.replace(",", "")
    try:
        return float(token)
    except ValueError:
        return None


def parse_income(value: Optional[str]) -> Optional[int]:
    """
    Parse an annual income cap from free text into an integer (₹).

    Examples:
        "₹2,50,000"      -> 250000
        "2.5 lakh"       -> 250000
        "Rs. 8 lakhs"    -> 800000
        "1 crore"        -> 10000000
        "no income limit"-> None
    """
    if value is None:
        return None
    text = str(value).lower()
    if not text.strip():
        return None
    if any(k in text for k in ("no income", "no limit", "not applicable", "n/a")):
        return None

    m = _NUM_RE.search(text)
    if not m:
        return None
    num = _to_number(m.group(1))
    if num is None:
        return None

    if "crore" in text:
        num *= 1_00_00_000
    elif "lakh" in text or "lac" in text:
        num *= 1_00_000

    return int(round(num))


# ── Age parsing ───────────────────────────────────────────────────────────

_AGE_RANGE_RE = re.compile(r"(\d{1,3})\s*(?:-|to|–|—|and)\s*(\d{1,3})")
_AGE_MIN_RE = re.compile(r"(?:above|over|minimum|atleast|at least|more than|>=?)\s*(\d{1,3})")
_AGE_MAX_RE = re.compile(r"(?:below|under|maximum|upto|up to|less than|<=?)\s*(\d{1,3})")


def parse_age_range(value: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    """
    Parse an (age_min, age_max) tuple from free text.

    Examples:
        "18 to 40 years"  -> (18, 40)
        "above 60"        -> (60, None)
        "up to 21 years"  -> (None, 21)
    """
    if not value:
        return (None, None)
    text = str(value).lower()

    m = _AGE_RANGE_RE.search(text)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        if lo > hi:
            lo, hi = hi, lo
        return (lo, hi)

    age_min = age_max = None
    mn = _AGE_MIN_RE.search(text)
    if mn:
        age_min = int(mn.group(1))
    mx = _AGE_MAX_RE.search(text)
    if mx:
        age_max = int(mx.group(1))
    return (age_min, age_max)


# ── Occupation / caste extraction (keyword tagging) ─────────────────────────

_OCCUPATION_KEYWORDS = {
    "Farmer": ["farmer", "agricultur", "kisan", "krishi", "cultivator"],
    "Student": ["student", "scholarship", "education", "pupil", "scholar"],
    "Business": ["business", "msme", "enterprise", "entrepreneur", "startup", "udyam"],
    "Salaried": ["salaried", "employee", "worker", "labour", "labor"],
    "Self-Employed": ["self-employed", "self employed", "artisan", "vishwakarma", "weaver"],
    "Unemployed": ["unemployed", "jobless", "skilling", "employment"],
    "Retired": ["retired", "pension", "senior citizen", "old age", "elderly"],
}

_CASTE_KEYWORDS = {
    "SC": ["scheduled caste", "sc ", "(sc)", "/sc"],
    "ST": ["scheduled tribe", "st ", "(st)", "/st", "tribal"],
    "OBC": ["obc", "other backward", "backward class"],
    "General": ["general category", "open category"],
    "EWS": ["ews", "economically weaker"],
}


def detect_occupations(text: Optional[str]) -> list[str]:
    """Tag the likely target occupations mentioned in scheme text."""
    if not text:
        return []
    low = str(text).lower()
    found = [occ for occ, kws in _OCCUPATION_KEYWORDS.items() if any(k in low for k in kws)]
    return found


def detect_caste_eligibility(text: Optional[str]) -> list[str]:
    """Tag the caste categories a scheme references."""
    if not text:
        return []
    low = str(text).lower()
    found = [cat for cat, kws in _CASTE_KEYWORDS.items() if any(k in low for k in kws)]
    return found
