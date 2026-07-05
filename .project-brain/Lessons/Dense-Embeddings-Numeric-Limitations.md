---
type: lesson
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[Eligibility-Engine]]"
  - "[[Brittle-Numeric-Vector-Search-Failure]]"
---

# Lesson: Dense Embeddings Numeric Limitations

## Context
When building a recommendation engine based on a vector database, developers often append demographic features directly to the semantic query, expecting the vector index to sort matches automatically.

---

## The Mistake
S.A.R.A.L. originally appended exact user incomes (e.g. `120000`) and ages to the Pinecone search queries.

---

## Why it Fails
Dense embedding models like `all-MiniLM-L6-v2` represent text in a high-dimensional vector space based on semantic context, not mathematical calculations.
* The embedding vectors for `"income 120000"` and `"income 180000"` are semantically similar.
* The model cannot evaluate logic like `User_Income (120000) <= Scheme_Limit (100000)`.
* Injecting exact digits introduces noise, causing the vector database to retrieve off-topic documents.

---

## The Correct Pattern
1. **Semantic Search:** Query vector databases using text-based conceptual terms (e.g. `"schemes for farming krishi subsidy"`).
2. **Metadata Pre-Filtering:** Filter categorical fields (like state or category) server-side inside the database.
3. **Structured Verification:** Let the LLM evaluate numeric constraints (like age and income bounds) in the final reasoning prompt.
