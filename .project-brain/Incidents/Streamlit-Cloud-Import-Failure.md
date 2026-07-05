---
type: incident
project: S.A.R.A.L.
status: resolved
confidence: confirmed
created: 2026-07-05
related:
  - "[[Streamlit-Interface]]"
  - "[[Direct-Service-Imports-Cloud-Mode]]"
caused_by:
  - "[[Streamlit-Cloud-Import-Failure]]"
---

# Incident: Streamlit Cloud Import Failure

## Context
During the initial deployment of S.A.R.A.L. to Streamlit Cloud, developers configured the Streamlit app to import services directly from the backend project folder (`from backend.app.services...`).

---

## Symptom
The deployment crashed immediately on launch, outputting a python error traceback:
`ModuleNotFoundError: No module named 'backend'`

---

## Initial Belief
It was believed that the `requirements.txt` was missing packages or that the backend folder was not being copied to the Streamlit runner container.

---

## Investigation & Root Cause
* **Investigation:** Inspected the Streamlit execution working directory.
* **Root Cause:** Streamlit Cloud runs Python from the parent folder of the targeted script. Since the main script was located in `frontend/app.py`, Streamlit set the working directory to `c:\Users\BAPS\OneDrive - pdpu.ac.in\Documents\AI_LAB_NEW\frontend`. As a result, the parent directory containing the `backend` folder was not in Python's search path (`sys.path`).

---

## Resolution Attempts
1. **Rearranging folders:** Attempted to move `app.py` to the project root. (Reverted in commit `1b5dae5`).
2. **System Path Injection:** Injected the project root directory into Python's path at runtime.

---

## Final Resolution
Modified [app.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/app.py) to explicitly prepend the parent project directory to `sys.path` before running any local imports:
```python
import os
import sys

# Get root directory and append to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
```

---

## Lessons Learned
Serverless platforms like Streamlit Cloud require explicit python path management at startup if components are nested inside subfolders.
* *Related note:* see **[[Direct-Service-Imports-Cloud-Mode]]**.
