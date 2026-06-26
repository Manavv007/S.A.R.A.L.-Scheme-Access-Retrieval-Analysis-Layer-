"""
Config-driven portal spider — covers state portals (and any HTML scheme
directory) without writing a new spider per site.

Reads `saral_scraper/portals.yaml`, where each portal declares its start URLs,
the CSS selectors to find scheme links, and the selectors to extract fields
from a detail page. Pages flagged `render: true` are fetched via Playwright.

Add a new state portal = add a YAML block. No code change required.

⚠️  The selectors in portals.yaml are templates and MUST be validated against
each live portal's DOM. Government sites vary widely and change over time.
"""

from __future__ import annotations

import os

import scrapy
import yaml

from saral_scraper.items import SchemeItem

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "portals.yaml")


class StatePortalsSpider(scrapy.Spider):
    name = "state_portals"

    def __init__(self, portal: str | None = None, *args, **kwargs):
        """`-a portal=gujarat` restricts the crawl to one configured portal."""
        super().__init__(*args, **kwargs)
        self.only_portal = portal
        self.portals = self._load_config()

    def _load_config(self) -> list[dict]:
        path = os.path.abspath(_CONFIG_PATH)
        if not os.path.exists(path):
            self.logger.error(f"[state_portals] config not found: {path}")
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        portals = data.get("portals", [])
        if self.only_portal:
            portals = [p for p in portals if p.get("name") == self.only_portal]
        return portals

    def start_requests(self):
        if not self.portals:
            self.logger.warning("[state_portals] No portals configured — nothing to crawl")
            return
        for portal in self.portals:
            for url in portal.get("start_urls", []):
                yield scrapy.Request(
                    url,
                    callback=self.parse_listing,
                    cb_kwargs={"portal": portal},
                    meta={"playwright": bool(portal.get("render"))},
                    dont_filter=True,
                )

    def parse_listing(self, response, portal: dict):
        sel = portal.get("selectors", {})
        link_sel = sel.get("scheme_link", 'a[href*="scheme"]::attr(href)')
        links = response.css(link_sel).getall()

        if not links:
            self.logger.warning(
                f"[state_portals:{portal.get('name')}] no scheme links via "
                f"'{link_sel}' — validate selectors against live DOM."
            )

        for href in links:
            yield response.follow(
                href,
                callback=self.parse_detail,
                cb_kwargs={"portal": portal},
                meta={"playwright": bool(portal.get("render"))},
            )

        # Optional pagination
        next_sel = sel.get("next_page")
        if next_sel:
            next_href = response.css(next_sel).get()
            if next_href:
                yield response.follow(
                    next_href,
                    callback=self.parse_listing,
                    cb_kwargs={"portal": portal},
                    meta={"playwright": bool(portal.get("render"))},
                )

    def parse_detail(self, response, portal: dict):
        sel = portal.get("selectors", {})

        def extract(key: str, default: str = "") -> str:
            css = sel.get(key)
            if not css:
                return default
            vals = response.css(css).getall()
            return " ".join(v.strip() for v in vals if v.strip()) or default

        name = extract("name")
        if not name:
            return

        item = SchemeItem()
        item["name"] = name
        item["level"] = portal.get("level", "State")
        item["state"] = portal.get("state")
        item["ministry"] = portal.get("ministry") or extract("ministry")
        item["benefits"] = extract("benefits")
        item["eligibility"] = extract("eligibility")
        item["description"] = extract("description")
        docs = extract("documents")
        item["documents_required"] = docs.split("|") if docs else []
        item["apply_url"] = extract("apply_url") or response.url
        item["source_url"] = response.url
        yield item
