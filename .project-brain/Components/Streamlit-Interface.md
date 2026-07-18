---
type: component
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[FastAPI-Backend]]"
  - "[[System-Overview]]"
  - "[[Direct-Service-Imports-Cloud-Mode]]"
  - "[[Streamlit-Cloud-Import-Failure]]"
---

# Streamlit Interface Component

The legacy Streamlit dashboard is implemented in [frontend/app.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/app.py). It serves as a secondary user interface and the primary deployment target for Hugging Face Spaces and Streamlit Cloud.

---

## 1. Key Roles and Architecture
The Streamlit app acts as the frontend orchestrator, rendering the citizen-facing controls and bridging to the AI services layer.

* **UI Renders:** Sidebar profile forms (age, state, caste, occupation, income) and a dual panel presenting matching scheme cards (3-column responsive layouts) alongside a rolling chatbot consultation frame.
* **Session State Management:** Retains user profile metadata, current recommendation lists, and chat context history across Streamlit's runtime page refreshes.

---

## 2. Backend Integration (HTTP-only)

> [!note] Updated 2026-07-18
> The earlier `LOCAL` vs `CLOUD` dual-execution behaviour has been **removed**. See superseded **[[Direct-Service-Imports-Cloud-Mode]]**.

The client in [api_client.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/src/utils/api_client.py) now **only** issues HTTP requests to the FastAPI backend — there is no in-memory service import branch:

```python
# api_client.py (current)
BASE_URL = (
    os.getenv("SARAL_API_BASE_URL")
    or os.getenv("BACKEND_URL")
    or "http://localhost:8000/api/v1"
).rstrip("/")

# All calls are HTTP:
response = requests.post(f"{BASE_URL}/recommend", json=profile, timeout=...)
response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=...)
```

* **Local dev:** points at `http://localhost:8000/api/v1` (FastAPI via `python -m backend.app.main`).
* **Streamlit Cloud / HF Spaces:** set `SARAL_API_BASE_URL` (or `BACKEND_URL`) to an externally hosted FastAPI URL. Streamlit no longer runs the backend in-process, so a reachable API host is required.
* `frontend/app.py` still prepends the project root to `sys.path`, but only to import its own `src.utils.api_client` helper — **not** backend service classes.

---

## 3. Historical Incidents & Modifications
* **Path Resolution Crashes:** Deployed versions frequently crashed due to `ModuleNotFoundError`. Fixes added dynamic project root injection at the very top of [app.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/app.py) (`sys.path.append(os.path.abspath(...))`). (See **[[Streamlit-Cloud-Import-Failure]]**).
* **Card Truncation Errors:** Custom CSS classes (`.scheme-card`) were updated to prevent text truncating or badge misalignment in high-dpi screens.
* **Deterministic LLM Settings:** Streamlit chat sessions was unified with the core FastAPI engine to enforce zero temperature to secure JSON-structured outputs.
