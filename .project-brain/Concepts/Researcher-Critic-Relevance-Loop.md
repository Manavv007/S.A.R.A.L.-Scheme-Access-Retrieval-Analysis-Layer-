---
type: concept
project: S.A.R.A.L.
status: active
confidence: confirmed
created: 2026-07-05
related:
  - "[[Eligibility-Engine]]"
  - "[[RAG-Retrieval-Augmented-Generation]]"
---

# Researcher-Critic Relevance Loop

## 1. What is the Researcher-Critic Loop?
Introduced as a Phase 2 upgrade in commit `cc5f1db`, the Researcher-Critic Relevance Loop is an agentic feedback cycle designed to check that retrieved documents match the user's domain before executing expensive eligibility evaluations.

---

## 2. Technical Process Flow
1. **Retrieve Initial Candidates:** The RAG retriever fetches candidate chunks from Pinecone.
2. **Critique:** The Critic LLM (`_CRITIC_PROMPT` in [recommendation.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/recommendation.py)) evaluates the first 8 chunks against user demographics.
3. **Verdict:**
   * **PASS:** If the retrieved documents are topically relevant, the loop terminates, and documents proceed to re-ranking.
   * **FAIL:** If off-topic, the Critic returns `FAIL` and proposes a `refined_query`.
4. **Refined Retrieval:** The system runs a search using the new query string and appends results to the document pool.
5. **Iteration:** The loop runs up to 3 times before falling open.

---

## 3. Why It Matters
Vector queries can pull irrelevant context due to semantic overlaps (e.g. searching for student aid might pull agricultural training schemes that mention "students"). The Critic acts as a fast semantic filter, identifying poor results early and refining search keywords to improve retrieval accuracy.
