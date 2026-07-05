---
type: timeline
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[System-Overview]]"
  - "[[PROJECT-BRAIN.md]]"
---

# Project Timeline

This is a chronological reconstruction of S.A.R.A.L.'s architecture, matching repository commits and pull request milestones to key design phases.

---

## Chronological Log

### Feb 17, 2026 — Project Bootstrapping
* **Initial State:** Empty repository.
* **Trigger:** Need a functional RAG search capability for Indian welfare schemes.
* **Change (`cb15d6b` - `b55aca0`):** Core RAG engine, Streamlit UI, initial prompt architectures, and documentation guidelines.
* **Result:** RAG model successfully queries Pinecone databases and answers user queries via Streamlit.

### Feb 18, 2026 — Dual-Query & State Boundaries
* **Initial State:** Base semantic vector searches match terms but miss state-specific restrictions.
* **Trigger:** Prevent recommending Gujarat schemes to residents of Maharashtra.
* **Change (`d2757e3`):** Implemented dual-query retrieval (fetching central and state schemes in parallel) and Python client-side state filtering.
* **Change (`7a2d880`):** Renamed the repository to S.A.R.A.L.

### Feb 19, 2026 — Streamlit Cloud Pathing and HF Spaces Sync Conflicts
* **Initial State:** REST-based calls crash on serverless Streamlit Cloud instances.
* **Trigger:** Enable Streamlit Cloud and Hugging Face Spaces deployments.
* **Change (`f48231f` - `c7fbbff`):** Built a monolithic direct import pathing adapter, hybrid config secret loaders, and prepended the root folder to `sys.path`. (See **[[Streamlit-Cloud-Import-Failure]]**).
* **Change (`18ab324` - `8f462cc`):** Configured GitHub Actions to sync with Hugging Face Spaces. Resolved divergent branch conflicts and file-size rejections using a clean force-push script. (See **[[Hugging-Face-Spaces-Push-Failure]]**).

### Feb 23, 2026 — Engine Determinism Tuning
* **Initial State:** LLM engines produce varied JSON formats, breaking frontend parsers.
* **Trigger:** Standardize recommendation responses.
* **Change (`f92e897`):** Set LLM engine temperature parameter to `0.0`. (See **[[Force-LLM-Determinism]]**).

### Apr 19, 2026 — Semantic Retrieval Hardening
* **Initial State:** User searches with exact income digits fail to return low-income schemes.
* **Trigger:** Dense embedding semantic search limitations.
* **Change (`f180838` - `6aa0c5b`):** Removed exact income values from vector search queries, shifted evaluations to metadata filtering, added strict occupation synonyms, and deduplicated sub-schemes by prefix. (See **[[Brittle-Numeric-Vector-Search-Failure]]**).

### Jun 26 - Jun 27, 2026 — Phase 2 Advanced Data Pipeline
* **Initial State:** Manual PDF processing and client-side Python filtering.
* **Trigger:** Need automated, incremental data collection and pre-filtering optimizations.
* **Change (`af2c2b2` - `cc5f1db`):** Deployed a Scrapy-Playwright crawler. Pushed state filters server-side to Pinecone, built the Researcher-Critic loop, candidate re-ranking, and grounded URL links. (See **[[Server-Side-Metadata-Filtering]]**).

### Jun 27 - Jun 28, 2026 — Next.js Migration and Hardening
* **Initial State:** Legacy python-only Streamlit UI.
* **Trigger:** Implement a premium user interface with streaming capabilities and rate limiting.
* **Change (`12f7e76` - `3c57129`):** Built a Next.js App Router frontend, streaming Route Handlers (BFF proxy), Redis caching, rate-limiting, and local voice speech features.
