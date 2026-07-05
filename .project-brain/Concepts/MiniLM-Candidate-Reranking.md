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

# MiniLM Candidate Re-Ranking

## 1. What is MiniLM Re-Ranking?
MiniLM Candidate Re-Ranking is a semantic relevance filter implemented in [recommendation.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/recommendation.py) to rank and select the top 15 retrieved document chunks from a candidate pool of 40.

---

## 2. Technical Implementation
1. **Local Vectors:** Reuses the HuggingFace `all-MiniLM-L6-v2` embeddings instance.
2. **Profile Vector Generation:** Embeds a combined profile query containing the user's occupation, state, income, and caste.
3. **Similarity Comparison:** Computes cosine similarity between the profile vector and the first 1000 characters of each candidate document.
   * *Formula:* Pure Python dot-product normalized by vector magnitude (`_cosine` helper method).
4. **Trimming:** Sorts matching documents in descending order and keeps the top 15 (`RERANK_TOP_N`), discarding the rest.

---

## 3. Why It Matters
While the initial multi-vector search maximizes recall by pulling central, state, and semantic matches, it introduces weaker context matches. Re-ranking ensures that the final LLM prompt context contains only high-relevance snippets, reducing token overhead and preventing hallucination.
