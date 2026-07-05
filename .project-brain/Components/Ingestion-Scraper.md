---
type: component
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[FastAPI-Backend]]"
  - "[[System-Overview]]"
  - "[[Server-Side-Metadata-Filtering]]"
---

# Ingestion & Scraper Component

Data scraping and ingestion pipelines are managed under the [scraper/](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/scraper/) directory. It represents a Phase 2 architectural improvement, transitioning S.A.R.A.L. from manual PDF ingestion to an automated, incremental scraping pipeline.

---

## 1. Spider Ingestion Architecture
* **Framework:** Scrapy + `ScrapyPlaywrightDownloadHandler` (Chromium integration to parse javascript-heavy portals like myScheme.gov.in).
* **Configuration ([settings.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/scraper/saral_scraper/settings.py)):** Configures user agent tags, download delays, and concurrent execution limits.

---

## 2. Ingestion Pipelines Chain ([pipelines.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/scraper/saral_scraper/pipelines.py))

All scraped scheme items are processed sequentially:

```
[ Scraped Raw Item ]
        │
        ▼
[ CleanPipeline ] ────▶ Strip HTML, normalize whitespace, extract age/income integers
        │
        ▼
[ ValidatePipeline ] ──▶ Drop items missing scheme name or substantive text contents
        │
        ▼
[ DuplicatesPipeline ] ▶ Drop scheme items already seen in the current crawl run
        │
        ▼
[ PineconePipeline ] ──▶ Chunk text -> Embed -> Idempotent upsert to Pinecone
```

### Key pipeline functions:
* **CleanPipeline:** Applies regex filters in [normalize.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/scraper/saral_scraper/normalize.py) to extract numerical thresholds (e.g. converting "Family income should be less than Rs. 2.5 Lakhs per annum" to `250000`).
* **DuplicatesPipeline:** Calculates deterministic scheme IDs (`make_scheme_id` in [scheme.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/models/scheme.py)) based on scheme level and state.
* **PineconePipeline:** Checks if the scheme data matches the database state to decide if re-embedding is required. If modified:
  * Generates structured text payloads summarizing scheme benefits, eligibility requirements, and documents.
  * Splitting payloads using `RecursiveCharacterTextSplitter` (`chunk_size=1000`, `overlap=200`).
  * Embeds text using `all-MiniLM-L6-v2` and upserts to Pinecone vector store under a deterministic ID schema (`sha1(f"{scheme_id}::{chunk_index}")`).

---

## 3. Incremental Crawling State ([statestore.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/scraper/saral_scraper/statestore.py))
To avoid excessive database costs and prevent duplicating embeddings, a local SQLite state database (`crawl_state.sqlite`) tracks:
* `{scheme_id: content_hash}`

During crawl iterations, the scraper compares computed content hashes against SQLite entries. Unchanged items are dropped (`DropItem`), skipping Pinecone API calls.
* *Detail decision:* see **[[Server-Side-Metadata-Filtering]]**.
