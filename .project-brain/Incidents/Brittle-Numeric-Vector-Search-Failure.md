---
type: incident
project: S.A.R.A.L.
status: resolved
confidence: confirmed
created: 2026-07-05
related:
  - "[[Eligibility-Engine]]"
  - "[[Dense-Embeddings-Numeric-Limitations]]"
---

# Incident: Brittle Numeric RAG Retrieval Failures

## Context
The system retrieves matching scheme documents by querying a Pinecone index using user demographic strings. Originally, the query string constructed in [recommendation.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/recommendation.py) appended the user's exact income:
`f"Government schemes for a {occupation} in {state} with income {income}"`

---

## Symptom
Users with low incomes (e.g. `50000`) were recommended schemes intended for citizens with higher incomes, while users with higher incomes (e.g., `800000`) were recommended low-income welfare schemes.

---

## Initial Belief
It was believed that the LLM prompt did not enforce income caps strictly enough. However, adjusting the prompt temperature and adding rules failed to resolve the issue.

---

## Investigation & Root Cause
* **Investigation:** Inspected the Pinecone retrieval scores and metadata.
* **Root Cause:** Dense text embedding models (like `all-MiniLM-L6-v2`) encode semantic concepts, not mathematical relationships. The embedding vector for the text `"income 150000"` is lexically close to `"income 250000"`, but the model cannot process the mathematical inequality `150000 < 250000`. The exact digits polluted the semantic search, causing Pinecone to retrieve off-topic documents.

---

## Resolution Attempts
1. **Adding strict rules to prompts:** Added negative constraints.
   * *Result:* Failed because the RAG retriever was not fetching the correct documents in the first place.
2. **Stripping income from vector search queries:** Wiped exact income numbers from the similarity search string.

---

## Final Resolution
* **Stripped Income from Vector Queries:** Modified [recommendation.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/recommendation.py) to exclude exact income amounts from search queries.
* **Server-side pre-filtering:** Relied on metadata filtering and explicit logical comparisons inside the LLM prompt to verify eligibility.

---

## Lessons Learned
Dense vector models should not be used to parse or search numeric ranges. Numerical constraints must be handled via metadata filters or logical LLM prompt instructions.
* *Related note:* see **[[Dense-Embeddings-Numeric-Limitations]]**.
