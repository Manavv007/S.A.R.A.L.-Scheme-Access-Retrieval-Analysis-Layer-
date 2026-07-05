---
type: unknown
project: S.A.R.A.L.
status: active
confidence: confirmed
created: 2026-07-05
related:
  - "[[PROJECT-BRAIN.md]]"
---

# Questions for Developer

These open questions identify gaps that cannot be resolved from the repository's Git logs or source configurations alone. Resolving them will clarify the deployment and operational profile of S.A.R.A.L.

---

## 1. n8n Automation Workflows Execution
The repository includes three automation configurations under [n8n-workflows/](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/n8n-workflows/):
* `workflow_whatsapp.json`
* `workflow_email_check.json`
* `workflow_db_sync.json`

**Questions:**
* How are these workflows hosted in production? (e.g. self-hosted n8n instance, n8n Cloud, or local desktop runtimes?)
* How do these integrations authenticate with S.A.R.A.L. API endpoints (especially when `SARAL_API_KEY` auth hardening is enabled)?

---

## 2. Pinecone Vector Database Scaling
* **Question:** What index configurations (e.g., number of pod replicas, similarity metric definitions, or pod type categories) are used for the production Pinecone index (`bharat-schemes`)?

---

## 3. Production Deployment Details
* **Question:** What is the primary domain/URL structure of the production Next.js frontend, and how does it relate to the Hugging Face Space URL (`https://manavv007-s-a-r-a-l.hf.space/`) which runs the Streamlit engine?
