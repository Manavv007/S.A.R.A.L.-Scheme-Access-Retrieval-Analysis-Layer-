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

## 1. Deployment Topology (HTTP-only)

> [!note] Updated 2026-07-18
> S.A.R.A.L. previously had a dual `DEPLOYMENT_ENV` topology (HTTP in `LOCAL`, in-memory imports in `CLOUD`). That was **removed** during the Next.js migration. All frontends now talk to FastAPI over HTTP only. See superseded **[[Direct-Service-Imports-Cloud-Mode]]**.

```
[ Next.js Web UI ] ──▶ (BFF API Proxy / Route Handlers) ─┐
                                                          │ (HTTP POST)
[ Streamlit Client ] ────────────────────────────────────┤
                                                          ▼
                                              [ FastAPI Web Server ]
                                                (port 8000, LOCAL / prod)
                                                          │
                                                          ▼
                                        [ Recommendation / RAG Services ]
```

* Both frontends ([NextJS-Frontend](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/web/src/app/page.tsx) and [Streamlit-Interface](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/app.py)) reach the backend over **HTTP REST** only.
* The Next.js app never calls FastAPI directly from the browser; it proxies through server-side **BFF Route Handlers** (hides the API base URL + keys, enables streaming). See **[[BFF-Proxy-Streaming-Chat-Decision]]**.
* The Streamlit app calls FastAPI directly via `SARAL_API_BASE_URL` / `BACKEND_URL` (default `http://localhost:8000/api/v1`).
* FastAPI coordinates all routing, rate-limiting, and caching. There is **no** in-process/monolithic import path (verified in `backend/app/main.py` and `frontend/src/utils/api_client.py`).
* For cloud deployments (Streamlit Cloud / HF Spaces), the frontend must be pointed at an externally hosted FastAPI URL — it can no longer run the backend in-process.

### Running Locally (one command)
A root launcher `start.bat` (added 2026-07-18) starts both processes in separate windows:
* Backend → `python -m backend.app.main` (FastAPI/uvicorn on `:8000`)
* Frontend → `web/` `npm run dev` (Next.js on `:3000`; auto-runs `npm install` on first run)

Double-click `start.bat` or run it from the repo root. The Streamlit UI remains available separately via `streamlit run frontend/app.py`.

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
