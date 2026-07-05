---
type: source
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[PROJECT-BRAIN.md]]"
  - "[[Project-Timeline]]"
---

# Source Evidence

This document links key historical and architectural assertions within the S.A.R.A.L. Project Brain back to physical repository sources and Git commit evidence.

---

## 1. Dual Deployment Mode
* **Assertion:** The system supports both local REST API routing and in-memory module imports for Streamlit Cloud.
* **Evidence:**
  * [api_client.py:L105-119](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/src/utils/api_client.py#L105-119): Switches logic based on `DEPLOYMENT_ENV == "CLOUD"`.
  * [app.py:L7-28](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/app.py#L7-28): Sets up system paths dynamically for in-memory importing.

---

## 2. Ingestion pipelines and SQLite State Cache
* **Assertion:** Ingestion checks content hash keys and skips re-indexing.
* **Evidence:**
  * [pipelines.py:L200-205](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/scraper/saral_scraper/pipelines.py#L200-205): Uses `self.store.has_changed()` to check hashes.
  * [statestore.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/scraper/saral_scraper/statestore.py): SQLite helper class writing to `crawl_state.sqlite`.

---

## 3. Server-side Pinecone Pre-filtering
* **Assertion:** State boundary logic is executed inside Pinecone rather than Python client-side post-retrieval.
* **Evidence:**
  * Commit `cc5f1db`: Pushed pre-filtering to Pinecone queries.
  * [recommendation.py:L230-248](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/recommendation.py#L230-248): Constructs metadata filters to check state and level.

---

## 4. Grounding and Deduplication
* **Assertion:** Scheme cards show apply/source URLs and sub-schemes are grouped by parent base names.
* **Evidence:**
  * [recommendation.py:L489-507](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/recommendation.py#L489-507): Deduplicates JSON lists using base scheme prefix regex splits.
  * [recommendation.py:L511-516](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/services/recommendation.py#L511-516): Searches source index dictionaries to assign `apply_url` and `source_url` fields.
