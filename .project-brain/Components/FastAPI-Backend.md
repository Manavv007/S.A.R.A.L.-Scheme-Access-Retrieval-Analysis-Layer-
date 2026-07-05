---
type: component
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[System-Overview]]"
  - "[[Eligibility-Engine]]"
  - "[[Ingestion-Scraper]]"
---

# FastAPI Backend Component

The backend intelligence layer is hosted under [backend/](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/) and runs on FastAPI. It acts as the API service provider, executing RAG lookups, managing config injection, and orchestrating security layers.

---

## 1. Directory Structure & Key Files
* **[main.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/main.py):** The entry point. Initializes the app, configures CORS (to permit cross-origin calls from Next.js), and mounts router endpoints.
* **[api/v1/](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/api/v1/):**
  * [chat.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/api/v1/chat.py): Exposes POST endpoints for chat and streaming `/chat/stream` using FastAPI's `StreamingResponse`.
  * [schemes.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/api/v1/schemes.py): Exposes POST endpoints for `/recommend` with recommendations cached.
  * [admin.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/api/v1/admin.py): Exposes crawl-observability endpoints, displaying histories from the SQLite crawl DB.
* **[core/](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/core/):**
  * [config.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/core/config.py): Config settings resolver that merges environment configurations and Streamlit secrets.
  * [security.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/core/security.py): Rate-limiting and header-based API key checks.
  * [cache.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/core/cache.py): Implements a hybrid cache manager (uses Redis when available; falls back to an in-memory dictionary cache).

---

## 2. Hardening & Mid-Layers

### A. Rate Limiting Middleware ([security.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/core/security.py))
* Uses a sliding fixed-window algorithm to track client IPs using memory dictionaries.
* Configured using `SARAL_RATE_LIMIT` (defaulting to 60 requests/minute). When exceeded, returns HTTP 429.

### B. API-Key Auth Dependency
* Routes inside `/api/v1/` require an `X-API-Key` matching `SARAL_API_KEY`.
* If `SARAL_API_KEY` is not set in environment settings, security checks are skipped, facilitating simple local development.

### C. Recommendation Caching ([cache.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/core/cache.py))
* Matches demographic inputs against a SHA-1 key (`Cache.make_key`) and caches JSON results for 1 hour (`_RECOMMEND_TTL`). This prevents duplicate vector evaluations and reduces LLM pricing costs.

---

## 3. Data Flow

```
[ Request ] ──▶ [ RateLimitMiddleware ] ──▶ [ require_api_key ]
                                                    │ (Pass)
                                                    ▼
                                            [ Schemes Router ]
                                                    │
                                            (Check Cache Key)
                                          /                   \
                                    (Hit) /                     \ (Miss)
                                         ▼                       ▼
                              [ Return Cached JSON ]     [ RecommendationService ]
                                                                 │
                                                       (Compute & Cache Result)
```
