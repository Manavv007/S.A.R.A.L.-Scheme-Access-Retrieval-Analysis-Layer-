"""Standalone test for the verified-scope hint (Layer 2).

Run with plain Python (no venv needed): python test_eligibility.py
Imports ONLY backend.app.services.eligibility, which is stdlib-only and makes
no network/Groq/Pinecone calls -- runs anywhere instantly.

Key regression covered: a SPECIFIC scheme (Krishi Yantra, Rajasthan-only) must
NOT be falsely matched by other schemes like "Atma Nirbhar Krishi Yojana" or
"Krishi Mahotsav Yojana" (the bug found in live testing).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(BACKEND, ".."))
for p in (ROOT, BACKEND):
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app.services.eligibility import scope_hint


PROFILE_GUJARAT_GENERAL = {
    "age": 34,
    "occupation": "Farmer",
    "state": "Gujarat",
    "income": "100000",
    "caste": "General",
}


def expect(name: str, cond: bool) -> None:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}")
    if not cond:
        globals()["_FAILED"] = True


def run() -> None:
    globals()["_FAILED"] = False

    # 1) The original failing case: Gujarat citizen asks about Krishi Yantra.
    hint = scope_hint(PROFILE_GUJARAT_GENERAL, "why am I not eligible for krishi yantra scheme?")
    expect("Krishi Yantra (Gujarat) yields a Rajasthan-only scope fact",
           bool(hint) and "Rajasthan" in hint and "Mukhyamantri" in hint)

    # 2) The headline REGRESSION: other "Krishi Yojana" schemes must NOT match.
    expect("'Atma Nirbhar Krishi Yojana' does NOT trigger Krishi Yantra fact",
           scope_hint(PROFILE_GUJARAT_GENERAL, "why eligible for Atma Nirbhar Krishi Yojana?") is None)
    expect("'Krishi Mahotsav Yojana' does NOT trigger Krishi Yantra fact",
           scope_hint(PROFILE_GUJARAT_GENERAL, "tell me about Krishi Mahotsav Yojana Gujarat") is None)
    expect("'Atma Nirbhar Krishi Yojana state?' returns None (no false fact)",
           scope_hint(PROFILE_GUJARAT_GENERAL, "Atma Nirbhar Krishi Yojana is in which state?") is None)

    # 3) Colloquial specific alias still matches (kisan yantra = distinctive).
    expect("colloquial 'kisan yantra' matched",
           bool(scope_hint(PROFILE_GUJARAT_GENERAL, "kisan yantra subsidy?")))

    # 4) Generic phrase MUST NOT match (this was the original bug source).
    expect("generic 'krishi yojana' alone does NOT match",
           scope_hint(PROFILE_GUJARAT_GENERAL, "krishi yojana details") is None)

    # 5) Rajasthan citizen still matches (hint is scheme-only, not a verdict).
    rajasthan = dict(PROFILE_GUJARAT_GENERAL, state="Rajasthan")
    expect("Rajasthan citizen -> hint still returned (scheme-only fact)",
           bool(scope_hint(rajasthan, "am I eligible for krishi yantra?")))

    # 6) Plain profile question -> None (not a scheme).
    expect("plain profile question -> None",
           scope_hint(PROFILE_GUJARAT_GENERAL, "what is my income?") is None)

    # 7) Empty/garbled profile must never crash.
    expect("None profile does not raise",
           scope_hint(None, "krishi yantra?") is None or isinstance(scope_hint(None, "krishi yantra?"), str))

    if globals()["_FAILED"]:
        print("\nRESULT: FAIL")
        sys.exit(1)
    print("\nRESULT: ALL PASS")


if __name__ == "__main__":
    run()
