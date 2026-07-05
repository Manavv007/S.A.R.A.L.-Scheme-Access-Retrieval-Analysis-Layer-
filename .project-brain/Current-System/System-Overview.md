---
type: concept
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[FastAPI-Backend]]"
  - "[[NextJS-Frontend]]"
  - "[[Streamlit-Interface]]"
  - "[[Eligibility-Engine]]"
  - "[[Ingestion-Scraper]]"
---

# System Overview

S.A.R.A.L. is designed as a modular Indian Government Scheme recommendation and consultation assistant. Its core goal is to run a high-fidelity **Retrieval-Augmented Generation (RAG)** pipeline that applies strict location and demographic constraints.

---

## 1. Dual Deployment Topologies

S.A.R.A.L. is designed to work in two separate deployment environments, configured via the `DEPLOYMENT_ENV` environment variable:

```
[ Next.js Web UI / Client ] ────▶ (BFF API Proxy / Route Handlers)
                                              │ (HTTP POST)
                                              ▼
                                   [ FastAPI Web Server ]
                                     (Local / Production)
                                              │
                                              ▼
[ Streamlit Client ] ─────────────────────────┼──▶ (HTTP POST in LOCAL mode)
                     -. (Direct Imports) .-.─▶ [ Recommendation / RAG Services ]
                         (In-Memory in CLOUD mode)
```

### A. Local Mode (Distributed HTTP)
* The frontend ([NextJS-Frontend](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/web/src/app/page.tsx) or [Streamlit-Interface](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/app.py) in `LOCAL` mode) makes standard HTTP REST calls to the FastAPI backend running on port `8000`.
* FastAPI coordinates all routing, rate-limiting, and caching.

### B. Cloud Mode (Monolithic / Serverless Fallback)
* When deployed on **Streamlit Cloud** (`DEPLOYMENT_ENV="CLOUD"`), starting and maintaining a separate FastAPI web service background process is restricted.
* The frontend [api_client.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/src/utils/api_client.py) dynamically imports the backend service layers (e.g. `RecommendationService`, `RAGService`) in-memory, bypassing the network loop.
* Set up in [app.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/app.py), path environment adjustments (`sys.path.append`) are injected at runtime.
* *Detail decision:* see **[[Direct-Service-Imports-Cloud-Mode]]**.

---

## 2. Core Operational Pipelines

### A. Ingestion & Pre-Processing Pipeline
1. The Scrapy-Playwright crawler in [scraper/](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/scraper/) crawls government portals.
2. Documents are parsed, stripped of HTML, and mapped to a canonical schema ([pipelines.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/scraper/saral_scraper/pipelines.py)).
3. Chunks are embedded locally via `all-MiniLM-L6-v2` and upserted to Pinecone.
4. Identical content is skipped using SQLite (`crawl_state.sqlite`) to make ingestion idempotent and prevent duplications.

### B. Recommendation & Verification Pipeline
1. The user submits a demographic profile (age, caste, state, occupation, income).
2. The [Eligibility-Engine](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/recommendation.py) issues three parallel queries to Pinecone to search central, state, and semantic concepts.
3. Pinecone filters out irrelevant states server-side (pre-filtering).
4. The **Researcher-Critic relevance loop** reviews the returned text snippets and requests query refinement if topically irrelevant.
5. The remaining candidates are re-ranked using cosine similarity of the local embeddings model.
6. The verdict LLM evaluates eligibility rules (occupation limits, income limits, caste reservations), produces a JSON array, and grounds them with official URLs.
