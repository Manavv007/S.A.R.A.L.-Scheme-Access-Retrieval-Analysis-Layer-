---
type: decision
project: S.A.R.A.L.
status: superseded
confidence: confirmed
created: 2026-07-05
superseded: 2026-07-18
related:
  - "[[Streamlit-Interface]]"
  - "[[Streamlit-Cloud-Import-Failure]]"
  - "[[BFF-Proxy-Streaming-Chat-Decision]]"
---

> [!warning] SUPERSEDED (verified 2026-07-18)
> This dual-execution / in-memory-import design is **no longer in the codebase**. During the Next.js migration & hardening phase (commits `12f7e76` → `3c57129`, Jun 27-28 2026) the frontend↔backend boundary was made **HTTP-only**. There is no `DEPLOYMENT_ENV=CLOUD` branch and no in-process import path anymore.
>
> Current verified evidence:
> - `backend/app/main.py` docstring: *"Frontends call it over HTTP - there is no in-process 'monolithic' import path anymore."*
> - `frontend/src/utils/api_client.py`: *"The frontend talks to the backend over HTTP only."* — no `DEPLOYMENT_ENV` read, no `from backend.app.services...` import; it only issues `requests.post` to `SARAL_API_BASE_URL`/`BACKEND_URL` (default `http://localhost:8000/api/v1`).
>
> The note below is retained as **historical** design context (why the dual-mode existed Feb-Jun 2026) — not current architecture.

# Decision: Direct Service Imports in Streamlit Cloud Mode

## Context & Problem
FastAPI REST API servers cannot easily run as separate background processes on serverless hosting platforms like Streamlit Cloud.
In early development, the frontend client code was hardcoded to call port 8000 via HTTP, which crashed when deployed to serverless environments because the backend service was unreachable.

---

## Options Considered
1. **Always-On Backend Server (External):** Host the FastAPI app on an external server (e.g. Render, Railway) and point the Streamlit client there.
   * *Cons:* Increases infrastructure costs, latency, and operational complexity for developer sandboxes.
2. **Dynamic Dual Execution Mode:** Detect the runtime environment and switch between REST client calls and direct, in-memory imports of backend services.
   * *Pros:* Allows single-click Streamlit Cloud deployments while preserving local HTTP decoupling.

---

## Choice Made
* **Dual Execution Mode:** Programmed [api_client.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/src/utils/api_client.py) to read `DEPLOYMENT_ENV`.
* If set to `"CLOUD"`, the client imports the service classes (`RecommendationService`, `RAGService`) directly and calls their Python methods in-memory, bypassing FastAPI and port 8000.

---

## Trade-offs & Consequences
* **Pros:** Streamlit Cloud deployment functions out-of-the-box using Streamlit's secrets manager.
* **Cons:** Streamlit's environment must load the entire Python dependency tree (e.g., LangChain, PyTorch embeddings). This increases memory usage and cold-start times, and requires path resolution hacks (`sys.path.append`) inside the UI code.

---

## Why It Was Superseded (2026-07-18)
The heavy-dependency / cold-start cons above, combined with the Next.js migration adding a proper **BFF proxy** (see **[[BFF-Proxy-Streaming-Chat-Decision]]**), made the in-memory mode redundant. The team standardized on a single decoupled contract: **every frontend (Next.js + Streamlit) talks to FastAPI over HTTP**. Streamlit Cloud / HF Spaces deployments now point at an externally hosted FastAPI base URL via `SARAL_API_BASE_URL` / `BACKEND_URL` instead of importing services in-process. `frontend/app.py` still injects the project root into `sys.path`, but only to import its own `src.utils.api_client` helper — not backend service classes.
