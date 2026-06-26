"""
Programmatic entrypoint for the S.A.R.A.L. scraper.

Runs one or more spiders via Scrapy's CrawlerProcess (blocks until finished).
Used by the scheduled GitHub Actions workflow and for local runs.

Usage (from the `scraper/` directory):
    python run.py                       # run all spiders
    python run.py myscheme              # run a single spider
    python run.py myscheme state_portals
    SARAL_DRY_RUN=1 python run.py myscheme   # no Pinecone writes
"""

import os
import sys

# Ensure this project's package is importable when run as a script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# All spiders we know about (name -> import path).
ALL_SPIDERS = ["myscheme", "state_portals"]


def main(argv: list[str]) -> int:
    os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "saral_scraper.settings")
    settings = get_project_settings()

    requested = argv[1:] or ALL_SPIDERS
    unknown = [s for s in requested if s not in ALL_SPIDERS]
    if unknown:
        print(f"[run] Unknown spider(s): {unknown}. Known: {ALL_SPIDERS}")
        return 2

    process = CrawlerProcess(settings)
    for spider_name in requested:
        print(f"[run] Scheduling spider: {spider_name}")
        process.crawl(spider_name)

    process.start()  # blocks until all crawls complete
    print("[run] All crawls finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
