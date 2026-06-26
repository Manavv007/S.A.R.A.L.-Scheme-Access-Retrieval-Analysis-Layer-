# 🚀 S.A.R.A.L. — Plan to Best-in-Class

## 🎯 Guiding Principle
Fresh, trustworthy, structured data is the moat. We build the scraping + data pipeline first, harden retrieval, then put a premium Next.js skin on top, and finish with high-impact extras.

---

## 📅 Roadmap & Execution Checklist

### 🏁 Phase 0 — Foundations (Prerequisites)
- [x] **1. Make ingestion idempotent**
  - Update `ingest_pdfs.py` to use deterministic IDs instead of random/blank generation.
  - Generate IDs based on `sha1(f"{scheme_id}::{chunk_index}")`.
  - Implement Pinecone upsert logic so re-running overwrites existing entries rather than duplicating them.
- [x] **2. Define canonical Scheme schema**
  - Implement one single source of truth for the scraper, ingestion, and retrieval metadata.
  - Include fields: `scheme_id`, `name`, `level` (Central/State), `state`, `ministry`, `target_occupation[]`, `caste_eligibility[]`, `income_limit`, `age_min`, `age_max`, `benefits`, `documents_required[]`, `apply_url`, `source_url`, `last_seen`, `content_hash`.
- [x] **3. Decouple backend from monolithic "CLOUD" hack**
  - Promote FastAPI `/recommend` and `/chat` endpoints to be the real integration surface.
  - Remove direct backend service imports in `api_client.py` based on `DEPLOYMENT_ENV`.
  - Configure proper CORS settings to allow Next.js queries.
- [x] **4. Fix the README/reality gap**
  - Address the documented but missing "Researcher-Critic loop" in `recommendation.py` (slated to be fully built in Phase 2).

---

### 🕸️ Phase 1 — Scrapy Ingestion Service
- [x] **1. Setup top-level Scrapy project structure**
  - Initialize independent directory `/scraper` with `scrapy.cfg`, `saral_scraper/`, and `run.py`.
- [x] **2. Configure Scrapy-Playwright for JS-heavy portals**
  - Configure `AsyncioSelectorReactor` and `ScrapyPlaywrightDownloadHandler`.
  - Enable browser rendering only for JS-dependent pages using `meta={"playwright": True}`.
  - Hit direct JSON endpoints where available on myScheme.gov.in and other portals to save resources.
- [x] **3. Construct item pipeline chain**
  - [x] **CleanPipeline:** Strip HTML, normalize whitespace, parse age/income strings into numbers.
  - [x] **ValidatePipeline:** Drop items missing key fields like name or eligibility criteria.
  - [x] **DuplicatesPipeline:** Drop duplicate items within the same scrape run.
  - [x] **PineconePipeline:** Chunk, embed using consistency-aligned `all-MiniLM-L6-v2` model, and upsert by deterministic ID.
- [x] **4. Implement incremental crawling**
  - Add SQLite database to track `{scheme_id: content_hash, last_seen}`.
  - Compare hashes during runs to skip unchanged pages, avoiding duplicate Pinecone embeds and lowering costs.
- [x] **5. Setup Scheduling & Politeness**
  - Run via `CrawlerProcess` using a scheduled GitHub Actions workflow (daily/weekly).
  - Respect `robots.txt`, configure `DOWNLOAD_DELAY` + `AUTOTHROTTLE`, set custom User-Agent, and apply concurrency limits.

---

### 🧠 Phase 2 — Data Quality & Retrieval Upgrades
- [x] **1. Structured metadata filtering in Pinecone**
  - Store fields like state, level, occupation, income, and caste directly inside Pinecone metadata.
  - Replace current client-side python logic in `_filter_docs` with server-side metadata pre-filtering.
- [x] **2. Build the Researcher-Critic loop**
  - Introduce a Critic LLM step to judge relevance.
  - Auto-refine and retry querying Pinecone up to 3 times on initial mismatch.
- [x] **3. Integrate candidate re-ranking**
  - Add cross-encoder / LLM re-ranking step over retrieved candidate documents before sending them to the LLM to fit the best context.
- [x] **4. Implement verdict grounding**
  - Cite the original `source_url` and `apply_url` on every AI-rendered recommendation.

---

### 🎨 Phase 3 — Premium Next.js Frontend
- [ ] **1. UI/UX visual design revamp**
  - Build modern Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui application.
  - Add smooth micro-interactions via Framer Motion.
  - Create custom canvas/WebGL particle background with deep emerald/violet gradients over a near-black base (#0a0a0a).
- [ ] **2. Glassmorphic component layout**
  - Implement premium glassmorphic cards with animated eligibility badges, skeleton loaders, and a clean multi-step profile wizard.
- [ ] **3. Backend-for-Frontend (BFF) & streaming**
  - Proxy all FastAPI endpoints via Next.js Route Handlers to hide API keys.
  - Implement Server-Sent Events (SSE) / streaming response for the chat consultant so responses stream token-by-token.
- [ ] **4. Hosting & i18n migration**
  - Separate frontend deployment (Vercel) and backend server (e.g., HF Spaces Docker/Render/Railway).
  - Port multi-language support (6 languages) to `next-intl`.

---

### 🛡️ Phase 4 — Trust & Accessibility Enhancements
- [ ] **1. Actionability layer**
  - Include an "Apply on official portal" button for cards.
  - Provide a dynamically populated document checklist based on schema information.
- [ ] **2. "Near-miss" eligibility indicators**
  - Show schemes that the user *almost* qualifies for, explicitly stating the blocker (e.g., "Available only in Gujarat" or "Income limit exceeded by ₹5,000").
- [ ] **3. Voice input and audio read-aloud**
  - Add speech-to-text input for the chat interface.
  - Provide text-to-speech option to read out results aloud in the user's selected language.

---

### 📊 Phase 5 — Testing, Observability & Hardening
- [ ] **1. Comprehensive test suites**
  - Write unit tests for data pipelines, normalization rules, and `recommendation.py` parsing logic.
  - Implement Playwright/Cypress end-to-end user-flow smoke tests.
- [ ] **2. Observability & dashboards**
  - Introduce structured logging.
  - Design a lightweight crawl stats dashboard tracking additions/updates/failures.
- [ ] **3. Caching and security layers**
  - Configure Redis caching layer to lower LLM retrieval costs and execution times.
  - Secure FastAPI endpoints with authentication and rate-limiting.
