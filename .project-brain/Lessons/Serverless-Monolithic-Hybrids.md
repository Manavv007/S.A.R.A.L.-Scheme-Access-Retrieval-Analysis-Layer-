---
type: lesson
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[Streamlit-Interface]]"
  - "[[Direct-Service-Imports-Cloud-Mode]]"
---

# Lesson: Serverless Monolithic Hybrids

## Context
Deploying python web applications with decoupled FastAPI backends and Streamlit frontends is straightforward in local environments. However, serverless hosting platforms like Streamlit Cloud restrict hosting multi-process architectures.

---

## The Solution
To deploy the same codebase locally and in serverless environments, S.A.R.A.L. uses a hybrid integration adapter pattern:

```python
# frontend/src/utils/api_client.py
if DEPLOYMENT_ENV == "CLOUD":
    # Direct python module imports
    from backend.app.services.recommendation import RecommendationService
else:
    # Decoupled HTTP client requests
    response = requests.post(f"{BACKEND_URL}/recommend", json=payload)
```

---

## Insights
1. **Decoupled Business Logic:** Keep backend endpoints slim and encapsulate core workflows (like database queries and LLM prompts) inside dedicated service classes.
2. **Dynamic Configurations:** Abstract service configurations behind singletons (like [config.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/core/config.py)) that merge environment variables (`.env`) and cloud secrets manager structures (`st.secrets`) automatically.
3. **Path Management:** Serverless platforms run Python from script-specific directories, requiring explicit project root prepends to `sys.path`.
