---
type: component
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[FastAPI-Backend]]"
  - "[[System-Overview]]"
  - "[[Server-Side-Metadata-Filtering]]"
  - "[[Force-LLM-Determinism]]"
  - "[[Brittle-Numeric-Vector-Search-Failure]]"
---

# Eligibility Engine & RAG Services

The recommendation service in [recommendation.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/recommendation.py) and the RAG helper in [rag_retriever.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/rag_retriever.py) form the intelligent core of S.A.R.A.L., executing RAG search retrieval and parsing demographics to identify eligible welfare schemes.

---

## 1. Multi-Vector Retrieval Flow

To maximize retrieval coverage, the engine initiates three parallel query paths for every user request:

```
[ User Profile Input ]
        │
        ├── Strategy A: Semantic Match (Nuanced description searches)
        ├── Strategy B: Keyword Match (Target state & occupation search keywords)
        └── Strategy C: National Fallback (Central PM scheme lookups)
```

The resulting vector chunks are merged and deduplicated by evaluating the first 200 characters of each page's content.

---

## 2. Server-Side Metadata Pre-Filtering
Before the retrieved text is sent to the LLM, the engine applies Pinecone metadata filters to restrict search bounds:
* `state == User.state OR level == "Central" OR state == "Central"`
* This guarantees that state-level schemas are only recommended to residents of those states, reducing context size.

---

## 3. Researcher-Critic Relevance Loop
To prevent off-topic document retrieval from polluting the LLM prompt context:
1. Snippets are reviewed by a **Critic LLM Prompt** (`_CRITIC_PROMPT`).
2. The Critic passes/fails the search results based on topical relevance.
3. If it fails, the Critic generates a refined query string and retries Pinecone search (up to 3 times).

---

## 4. MiniLM Candidate Re-Ranking
Once relevant documents are retrieved:
1. The top 40 candidates are selected.
2. Cosine similarity is calculated locally using the `all-MiniLM-L6-v2` embedding vector space.
3. The top 15 matches (`RERANK_TOP_N`) are retained, discarding weaker text chunks.

---

## 5. Structured Verdict Ingestion & Grounding
* The 15 re-ranked contexts are injected into `_ELIGIBILITY_PROMPT` along with caste categories and occupation filters.
* Groq (`llama-3.3-70b-versatile`) processes the prompt with `temperature=0.0` to generate a structured JSON array detailing eligibility verdicts.
* **Grounding:** The service matches LLM scheme names with source metadata index values to attach direct `apply_url` and `source_url` fields.
* **Deduplication:** Sub-schemes are grouped by base prefixes (e.g. merging sub-schemes under "MSME") to prevent layout clutter.
