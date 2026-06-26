"""
myScheme spider — central + state schemes from https://www.myscheme.gov.in

myScheme is a JS-rendered (Next.js) portal backed by a JSON API. Two paths:

  1. JSON API (preferred — cheap, structured). The public site fetches from
     `https://api.myscheme.gov.in` with an `x-api-key` header. Set the key via
     the SARAL_MYSCHEME_API_KEY env var to use this path.

  2. Playwright fallback (no key). Renders the search results + detail pages in
     a headless browser and extracts from the DOM.

 Live-validation note: government portals change their API response shape and
DOM structure over time. The selectors / JSON keys below are defensive (multiple
fallbacks) but MUST be validated against the live site before a production run.
Run with `-L DEBUG` and inspect `_log_unknown_shape` output to adjust mappings.
"""

from __future__ import annotations

import json
import os

import scrapy

from saral_scraper.items import SchemeItem


class MySchemeSpider(scrapy.Spider):
    name = "myscheme"
    allowed_domains = ["myscheme.gov.in", "api.myscheme.gov.in"]

    API_BASE = "https://api.myscheme.gov.in"
    WEB_BASE = "https://www.myscheme.gov.in"
    PAGE_SIZE = 20

    def _api_key(self) -> str | None:
        return self.settings.get("SARAL_MYSCHEME_API_KEY") or os.getenv(
            "SARAL_MYSCHEME_API_KEY"
        )

    # ── Entry point ─────────────────────────────────────────────────────────
    def start_requests(self):
        key = self._api_key()
        if key:
            self.logger.info("[myscheme] Using JSON API path")
            yield self._api_list_request(frm=0, key=key)
        else:
            self.logger.info(
                "[myscheme] No SARAL_MYSCHEME_API_KEY set — using Playwright fallback"
            )
            yield scrapy.Request(
                f"{self.WEB_BASE}/search",
                callback=self.parse_listing_html,
                meta={"playwright": True, "playwright_include_page": False},
            )

    # ── JSON API path ─────────────────────────────────────────────────────
    def _api_list_request(self, frm: int, key: str) -> scrapy.Request:
        url = (
            f"{self.API_BASE}/search/v4/schemes"
            f"?lang=en&q=&keyword=&sort=&from={frm}&size={self.PAGE_SIZE}"
        )
        return scrapy.Request(
            url,
            callback=self.parse_listing_api,
            headers={"x-api-key": key, "accept": "application/json"},
            cb_kwargs={"frm": frm, "key": key},
            dont_filter=True,
        )

    def parse_listing_api(self, response, frm: int, key: str):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("[myscheme] API listing was not JSON; aborting API path")
            return

        # Defensive navigation across known response shapes.
        hits = (
            data.get("data", {}).get("hits", {}).get("items")
            or data.get("data", {}).get("hits")
            or data.get("hits")
            or []
        )
        if not isinstance(hits, list):
            self._log_unknown_shape("listing", data)
            return

        for hit in hits:
            fields = hit.get("fields", hit) if isinstance(hit, dict) else {}
            slug = (
                fields.get("slug")
                or fields.get("schemeShortTitle")
                or fields.get("schemeName")
            )
            if not slug:
                continue
            yield scrapy.Request(
                f"{self.API_BASE}/schemes/v4/public/schemes/{slug}",
                callback=self.parse_detail_api,
                headers={"x-api-key": key, "accept": "application/json"},
                cb_kwargs={"slug": slug},
            )

        # Paginate
        total = (
            data.get("data", {}).get("summary", {}).get("total")
            or data.get("total")
            or 0
        )
        next_frm = frm + self.PAGE_SIZE
        if next_frm < int(total or 0):
            yield self._api_list_request(frm=next_frm, key=key)

    def parse_detail_api(self, response, slug: str):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.warning(f"[myscheme] detail not JSON for slug={slug}")
            return

        d = data.get("data", data)
        # The detail payload commonly nests under 'en' / 'schemeContent'.
        en = d.get("en", d) if isinstance(d, dict) else {}
        basic = en.get("basicDetails", en) if isinstance(en, dict) else {}

        name = (
            basic.get("schemeName")
            or en.get("schemeName")
            or d.get("schemeName")
        )
        if not name:
            self._log_unknown_shape(f"detail:{slug}", data)
            return

        state = basic.get("state") or en.get("state")
        level = basic.get("level") or ("State" if state else "Central")

        item = SchemeItem()
        item["name"] = name
        item["level"] = level
        item["state"] = state
        item["ministry"] = basic.get("nodalMinistryName") or basic.get("ministry")
        item["benefits"] = self._join(en.get("schemeContent", {}).get("benefits"))
        item["eligibility"] = self._join(en.get("eligibilityCriteria", {}).get("eligibilityDescription"))
        item["description"] = self._join(en.get("schemeContent", {}).get("detailedDescription"))
        item["documents_required"] = en.get("applicationProcess", {}).get("documents") or []
        item["apply_url"] = f"{self.WEB_BASE}/schemes/{slug}"
        item["source_url"] = response.url
        yield item

    # ── Playwright HTML fallback ────────────────────────────────────────────
    def parse_listing_html(self, response):
        """
        Extract scheme detail links from the rendered search page and follow
        them. Selector is intentionally broad; validate against live DOM.
        """
        links = response.css('a[href*="/schemes/"]::attr(href)').getall()
        seen = set()
        for href in links:
            if not href or href in seen:
                continue
            seen.add(href)
            yield response.follow(
                href,
                callback=self.parse_detail_html,
                meta={"playwright": True},
            )
        if not links:
            self.logger.warning(
                "[myscheme] No scheme links found on rendered page — DOM selectors "
                "likely need updating for the current site version."
            )

    def parse_detail_html(self, response):
        name = (
            response.css("h1::text").get()
            or response.css('[class*="scheme"] h1::text').get()
        )
        if not name:
            return
        item = SchemeItem()
        item["name"] = name.strip()
        item["state"] = None
        item["level"] = "Central"
        # Best-effort section extraction; refine selectors against live DOM.
        item["benefits"] = self._section_text(response, "benefit")
        item["eligibility"] = self._section_text(response, "eligib")
        item["description"] = " ".join(response.css("p::text").getall()[:30])
        item["documents_required"] = []
        item["apply_url"] = response.url
        item["source_url"] = response.url
        yield item

    # ── helpers ──
    @staticmethod
    def _join(value) -> str:
        if isinstance(value, list):
            return " ".join(str(v) for v in value)
        return str(value or "")

    @staticmethod
    def _section_text(response, keyword: str) -> str:
        # Grab text from a section whose heading/class contains `keyword`.
        xpath = (
            f"//*[contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            f"'abcdefghijklmnopqrstuvwxyz'),'{keyword}')]//text()"
        )
        parts = response.xpath(xpath).getall()
        return " ".join(p.strip() for p in parts if p.strip())[:4000]

    def _log_unknown_shape(self, where: str, data) -> None:
        sample = json.dumps(data, ensure_ascii=False)[:800]
        self.logger.warning(
            f"[myscheme] Unrecognized JSON shape at {where}. "
            f"Adjust key mapping. Sample: {sample}"
        )
