"""
Scrapy settings for the S.A.R.A.L. scheme ingestion service.

Highlights:
  • scrapy-playwright download handlers (for JS-rendered government portals)
  • polite crawling defaults (robots.txt, autothrottle, delays, concurrency)
  • the Clean → Validate → Duplicates → Pinecone item-pipeline chain
  • a sys.path bootstrap so we can import the canonical Scheme schema from
    the backend package (single source of truth defined in Phase 0).
"""

import os
import sys

# ── Make the repo root importable so `backend.app.models.scheme` works ──────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Load .env at the repo root (Pinecone / model config) if python-dotenv present.
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(_REPO_ROOT, ".env"))
except Exception:
    pass

# ── Core Scrapy identity ────────────────────────────────────────────────────
BOT_NAME = "saral_scraper"
SPIDER_MODULES = ["saral_scraper.spiders"]
NEWSPIDER_MODULE = "saral_scraper.spiders"

# ── Politeness (be a good citizen on government infrastructure) ─────────────
ROBOTSTXT_OBEY = True
USER_AGENT = os.getenv(
    "SARAL_USER_AGENT",
    "SARAL-SchemeBot/1.0 (+https://github.com/; civic scheme discovery; contact: admin@example.com)",
)

DOWNLOAD_DELAY = float(os.getenv("SARAL_DOWNLOAD_DELAY", "1.5"))
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 30.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.5

# Cache responses during development to avoid re-hitting portals.
HTTPCACHE_ENABLED = os.getenv("SARAL_HTTPCACHE", "0") == "1"
HTTPCACHE_EXPIRATION_SECS = 86400

RETRY_ENABLED = True
RETRY_TIMES = 2

# ── scrapy-playwright (JS rendering) ────────────────────────────────────────
# Per scrapy-playwright docs: use the asyncio reactor + custom download handlers.
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

PLAYWRIGHT_BROWSER_TYPE = os.getenv("SARAL_PLAYWRIGHT_BROWSER", "chromium")
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
}
# Abort the navigation if a page takes too long to render.
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30_000  # ms

# ── Item pipeline chain (executed in ascending order) ───────────────────────
ITEM_PIPELINES = {
    "saral_scraper.pipelines.CleanPipeline": 100,
    "saral_scraper.pipelines.ValidatePipeline": 200,
    "saral_scraper.pipelines.DuplicatesPipeline": 300,
    "saral_scraper.pipelines.PineconePipeline": 400,
}

# ── Project-specific knobs (read by pipelines) ──────────────────────────────
# Embedding model MUST match the one used at query time in rag_retriever.py.
SARAL_EMBED_MODEL = os.getenv("SARAL_EMBED_MODEL", "all-MiniLM-L6-v2")
SARAL_CHUNK_SIZE = int(os.getenv("SARAL_CHUNK_SIZE", "1000"))
SARAL_CHUNK_OVERLAP = int(os.getenv("SARAL_CHUNK_OVERLAP", "200"))
SARAL_PINECONE_INDEX = os.getenv("PINECONE_INDEX_NAME", "bharat-schemes")
# SQLite file backing incremental crawl change-detection.
SARAL_STATE_DB = os.getenv(
    "SARAL_STATE_DB", os.path.join(_REPO_ROOT, "data", "processed", "crawl_state.sqlite")
)
# Set to "1" to skip writing to Pinecone (dry run; still updates state DB off).
SARAL_DRY_RUN = os.getenv("SARAL_DRY_RUN", "0") == "1"

# ── Misc ────────────────────────────────────────────────────────────────────
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = os.getenv("SARAL_LOG_LEVEL", "INFO")
