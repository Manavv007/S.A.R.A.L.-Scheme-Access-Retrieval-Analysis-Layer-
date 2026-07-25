"""
Deterministic, profile-grounded SCOPE HINTS (Layer 2 of the profile-grounded
fusion architecture).

DESIGN INTENT (product owner): the chatbot is a HELPFUL ASSISTANT that answers
about ANY scheme from its knowledge (RAG + general knowledge). It must NOT
return hardcoded / predefined answers. So this module does NOT produce verdicts
like "You are not eligible for X". Instead it returns a short, verified FACT
about a scheme's scope (e.g. "available only in Rajasthan") that is injected
into the LLM prompt as a hint. The LLM then answers naturally, in the user's
language, combining the fact with the citizen form.

This avoids two failure modes that were seen in testing:
  * The old refusal bug: LLM said "I don't have enough info" when RAG was empty.
    (Fixed at the prompt layer; this hint just makes scope facts reliable.)
  * Over-triggering: matching must be SCHEME-SPECIFIC. A generic alias like
    "krishi yojana" wrongly fired on "Atma Nirbhar Krishi Yojana". We match on
    distinctive tokens / exact specific phrases only, so other schemes are
    never affected and never receive a false fact.

Coverage: state-restricted and category-reserved schemes listed in the registry.
Add a scheme here the moment it causes trouble in testing.
"""

from __future__ import annotations

import re

# Generic words that appear in many scheme names and must NOT alone identify a
# scheme. Matching requires distinctive tokens (e.g. yantra, anudan) or an
# exact specific phrase.
_GENERIC = {"krishi", "yojana", "scheme", "the", "of", "a", "an", "and", "for"}

# Curated scheme scope registry. `aliases` are SPECIFIC phrases (substring
# matched against the normalized query). `key_tokens` are distinctive words; a
# query must contain >=2 of them to match (prevents "X Krishi Yojana" from
# matching a different scheme).
_SCHEME_REGISTRY: list[dict] = [
    {
        "name": "Mukhyamantri Krishi Yantra Anudan Yojana",
        "aliases": [
            "mukhyamantri krishi yantra",
            "krishi yantra anudan",
            "krishi yantra anudan yojana",
            "kisan yantra",
            "krishi yantra",
        ],
        "key_tokens": {"yantra", "anudan", "mukhyamantri"},
        "states": ["Rajasthan"],
        "categories": None,
    },
]


def _norm(text) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def _tokens(text: str) -> set[str]:
    return {t for t in _norm(text).split() if len(t) > 2 and t not in _GENERIC}


def _match_scheme(query: str) -> dict | None:
    """Return the registry entry precisely mentioned in *query*, else None."""
    q = _norm(query)
    if not q:
        return None
    for entry in _SCHEME_REGISTRY:
        # 1) Exact specific-phrase match (aliases are deliberately specific).
        for alias in entry.get("aliases", []):
            if _norm(alias) in q:
                return entry
        # 2) Distinctive token overlap (>=2 key tokens). Generic tokens like
        #    "krishi"/"yojana" are excluded so other schemes don't collide.
        key = entry.get("key_tokens") or set()
        if key and len(key & _tokens(q)) >= 2:
            return entry
    return None


def scope_hint(profile: dict | None, query: str) -> str | None:
    """Return a verified SCOPE FACT for a matched scheme, else None.

    The fact is scheme-only (no user-state verdict), so it is safe to inject
    into the LLM prompt as a hint. Returns None when no registered scheme is
    precisely mentioned, letting the LLM answer from its own knowledge.
    """
    entry = _match_scheme(query)
    if not entry:
        return None
    states = entry.get("states")
    cats = entry.get("categories")
    if states:
        return (
            f"Verified scope: '{entry['name']}' is available only in "
            f"{', '.join(states)}."
        )
    if cats:
        return (
            f"Verified scope: '{entry['name']}' is reserved for "
            f"{', '.join(cats)} categories."
        )
    return None
