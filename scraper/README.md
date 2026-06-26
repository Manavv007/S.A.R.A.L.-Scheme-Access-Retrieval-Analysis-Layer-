# S.A.R.A.L. Scheme Scraper

Scrapy ingestion service that discovers **Central + State** government schemes,
normalizes them to the canonical `Scheme` schema, and **incrementally** upserts
them into Pinecone — so new/changed schemes show up in the RAG index automatically.

## How it fits together

```
spiders (myscheme / state_portals)
        │  yield SchemeItem
        ▼
CleanPipeline ─► ValidatePipeline ─► DuplicatesPipeline ─► PineconePipeline
  (normalize)       (drop empty)        (dedupe run)         (chunk→embed→upsert)
                                                                   │
                                                      SQLite state (skip unchanged)
                                                      Pinecone (deterministic ids)
```

- **Single source of truth:** items map onto `backend/app/models/scheme.py`.
- **Idempotent:** vectors use `vector_id(scheme_id, chunk_index)` so re-ingestion
  overwrites instead of duplicating (same guarantee as the PDF ingester).
- **Incremental:** `statestore.py` (SQLite) records each scheme's content hash;
  unchanged schemes are dropped before any embedding/Pinecone work.

## Setup

```bash
pip install -r backend/requirements.txt
pip install -r scraper/requirements.txt
python -m playwright install chromium
```

Environment (reads the repo-root `.env`):

| Variable                  | Purpose                                            |
|---------------------------|----------------------------------------------------|
| `PINECONE_API_KEY`        | Pinecone auth (required for live writes)           |
| `PINECONE_INDEX_NAME`     | Target index (default `bharat-schemes`)            |
| `SARAL_MYSCHEME_API_KEY`  | Enables the myScheme JSON API path (optional)      |
| `SARAL_DRY_RUN=1`         | Parse only; no Pinecone writes                     |
| `SARAL_STATE_DB`          | Path to the incremental-crawl SQLite file          |
| `SARAL_DOWNLOAD_DELAY`    | Per-request delay seconds (default 1.5)            |

## Running

```bash
cd scraper

# Dry run (no writes) — recommended first, to validate parsing/selectors:
SARAL_DRY_RUN=1 python run.py myscheme

# Full run, all spiders:
python run.py

# Single configured state portal:
scrapy crawl state_portals -a portal=gujarat -L DEBUG
```

## Politeness

`ROBOTSTXT_OBEY=True`, autothrottle on, `DOWNLOAD_DELAY=1.5s`, max 2 concurrent
requests per domain, and a descriptive `USER_AGENT`. Be respectful of government
infrastructure and check each portal's terms before enabling it.

## ⚠️ Selector / API-shape validation

Spider selectors and the myScheme JSON key mappings are **defensive templates**.
Government portals change structure over time, so before a production run:

1. Run with `SARAL_DRY_RUN=1 ... -L DEBUG`.
2. Watch for `Unrecognized JSON shape` / `no scheme links` warnings.
3. Adjust `spiders/myscheme.py` key mappings or `portals.yaml` selectors.

Add a new state portal by appending a block to `portals.yaml` — no code change.

## Scheduling

`.github/workflows/scrape.yml` runs the crawler daily (central) and weekly
(incl. state), caching the SQLite state between runs. Configure repo secrets:
`PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, and optionally `SARAL_MYSCHEME_API_KEY`.
