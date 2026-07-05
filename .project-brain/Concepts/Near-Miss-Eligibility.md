---
type: concept
project: S.A.R.A.L.
status: active
confidence: confirmed
created: 2026-07-05
related:
  - "[[Eligibility-Engine]]"
---

# Near-Miss Eligibility

## 1. What is Near-Miss Eligibility?
Near-Miss Eligibility is a Phase 4 feature designed to show users schemes they *almost* qualify for, identifying the single blocker preventing matching.

---

## 2. Implementation Logic
* Inside `_ELIGIBILITY_PROMPT` in [recommendation.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/recommendation.py), the LLM is instructed to identify:
  1. **Eligible Schemes:** Schemes where the user satisfies all criteria.
  2. **Near-Miss Schemes:** Schemes where the user satisfies all but one criterion.
* The response JSON array returns an `eligibility_status` of `"Near-Miss"` and documents the blocker under `reason` (e.g. `"Income exceeds limit by Rs. 15,000"` or `"Available only in Gujarat"`).
* Schemes targeting different profiles (e.g. suggesting business subsidies to a student) are excluded from the near-miss output.

---

## 3. Why It Matters
Standard filters reject mismatching profiles silently. Near-Miss indicators prevent "no schemes found" screens and provide transparency, showing users what parameters (such as minor age limits or residency state) block eligibility.
