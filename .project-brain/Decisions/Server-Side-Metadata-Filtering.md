---
type: decision
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[Eligibility-Engine]]"
  - "[[Ingestion-Scraper]]"
---

# Decision: Server-Side Metadata Filtering in Pinecone

## Context & Problem
Originally, S.A.R.A.L. fetched a large pool of candidate documents from Pinecone and filtered out mismatching state levels in Python. This client-side post-filtering caused issues:
1. It wasted LLM tokens and vector retrieval calls on ineligible documents.
2. If all retrieved candidates belonged to other states, the filter dropped them all, returning zero documents and causing recommendation failures.

---

## Options Considered
1. **Client-Side Python Filtering:** Keep post-filtering logic in python.
   * *Cons:* Brittle and expensive.
2. **Server-Side Metadata Pre-Filtering:** Attach state tags directly to Pinecone vector metadata during ingestion and filter them during the similarity query phase.
   * *Pros:* Ensures all documents returned by Pinecone match the user's location, reducing downstream overhead.

---

## Choice Made
* **Server-Side Metadata Pre-Filtering:** Implemented in [recommendation.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/recommendation.py) and supported by schema updates in [pipelines.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/scraper/saral_scraper/pipelines.py).
* The query includes a `$or` metadata filter:
  ```json
  {
    "$or": [
      {"level": {"$eq": "Central"}},
      {"state": {"$eq": "Central"}},
      {"state": {"$eq": profile.state}}
    ]
  }
  ```

---

## Trade-offs & Consequences
* **Pros:** Guarantees that Pinecone returns only central schemes or state-matched schemes. Reduces RAG token costs and eliminates cross-state recommendations.
* **Cons:** Requires strict adherence to metadata naming conventions during scraping/ingestion. Legacy embeddings that lack the `level` or `state` fields can get filtered out, requiring database rebuilds.
