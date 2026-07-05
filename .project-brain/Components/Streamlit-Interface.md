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

## 2. Integration Modes (`LOCAL` vs. `CLOUD`)

The client adapts dynamically using [api_client.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/src/utils/api_client.py):

```python
# Dual-Execution configuration in api_client.py
if DEPLOYMENT_ENV == "CLOUD":
    # direct in-memory calls
    from backend.app.services.recommendation import RecommendationService
    ...
else:
    # HTTP REST requests
    response = requests.post(f"{BACKEND_URL}/recommend", json=profile)
```

### A. Local HTTP execution
* Renders fields and relays requests as standard JSON payloads to the FastAPI REST API.

### B. Cloud monolithic execution
* Solves serverless hosting restrictions on Streamlit Cloud by importing services directly (`from backend.app.services...`).
* Injects environment secrets directly at startup:
  ```python
  # Inject secrets from Streamlit secrets file into OS environment for LangChain
  for key in ["PINECONE_API_KEY", "GROQ_API_KEY"]:
      if key in st.secrets:
          os.environ[key] = st.secrets[key]
  ```

---

## 3. Historical Incidents & Modifications
* **Path Resolution Crashes:** Deployed versions frequently crashed due to `ModuleNotFoundError`. Fixes added dynamic project root injection at the very top of [app.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/app.py) (`sys.path.append(os.path.abspath(...))`). (See **[[Streamlit-Cloud-Import-Failure]]**).
* **Card Truncation Errors:** Custom CSS classes (`.scheme-card`) were updated to prevent text truncating or badge misalignment in high-dpi screens.
* **Deterministic LLM Settings:** Streamlit chat sessions was unified with the core FastAPI engine to enforce zero temperature to secure JSON-structured outputs.
