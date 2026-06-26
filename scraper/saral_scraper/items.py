"""
Scrapy items for the S.A.R.A.L. scraper.

`SchemeItem` mirrors the canonical `backend.app.models.scheme.Scheme` fields,
plus a few *raw* fields (eligibility / description text) that the CleanPipeline
uses to derive the structured values and the text we embed.
"""

import scrapy


class SchemeItem(scrapy.Item):
    # ── Canonical fields (align with backend Scheme) ──
    name = scrapy.Field()
    level = scrapy.Field()                 # "Central" | "State"
    state = scrapy.Field()
    ministry = scrapy.Field()
    target_occupation = scrapy.Field()     # list[str]
    caste_eligibility = scrapy.Field()     # list[str]
    income_limit = scrapy.Field()          # int | None
    age_min = scrapy.Field()               # int | None
    age_max = scrapy.Field()               # int | None
    benefits = scrapy.Field()
    documents_required = scrapy.Field()    # list[str]
    apply_url = scrapy.Field()
    source_url = scrapy.Field()

    # ── Raw text used for normalization + embedding ──
    eligibility = scrapy.Field()           # raw eligibility text
    description = scrapy.Field()           # full scheme description / details
