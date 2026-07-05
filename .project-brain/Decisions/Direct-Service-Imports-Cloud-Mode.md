---
type: decision
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[Streamlit-Interface]]"
  - "[[Streamlit-Cloud-Import-Failure]]"
---

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
