---
type: decision
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[Eligibility-Engine]]"
  - "[[Brittle-Numeric-Vector-Search-Failure]]"
---

# Decision: Enforcing LLM Engine Determinism

## Context & Problem
In early iterations, the LLM Engine Wrapper used the default temperature settings (typically `0.7` to `1.0`). When evaluating eligibility, this caused issues:
1. The model would generate varied JSON keys or add conversational markdown wrap text, breaking JSON parsers.
2. The eligibility status would flip between "Eligible" and "Near-Miss" for identical user profiles on successive runs, degrading user trust.

---

## Options Considered
1. **High/Medium Temperature (0.7) with Schema Checking:** Attempt to validate and repair varied JSON structures in python post-processing.
   * *Cons:* Brittle and doesn't solve contradictory eligibility decisions.
2. **Zero Temperature (0.0):** Force the model to select the highest-probability token at each step, ensuring consistent outputs.
   * *Pros:* Standard practice for structured data extraction and logical reasoning tasks.

---

## Choice Made
* **Zero Temperature:** Set `temperature=0.0` inside [llm_engine.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/llm_engine.py) when instantiating `ChatGroq`.

---

## Trade-offs & Consequences
* **Pros:** Standardizes JSON structures, making responses predictable and parsable.
* **Cons:** Chatbot responses in `/chat` can feel slightly repetitive, as the model uses deterministic responses for identical conversational prompts.
