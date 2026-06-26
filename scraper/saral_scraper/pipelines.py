"""
Item pipeline chain for the S.A.R.A.L. scraper.

Order (configured in settings.py):
    CleanPipeline (100) → ValidatePipeline (200)
    → DuplicatesPipeline (300) → PineconePipeline (400)

Each component implements ``process_item`` and either returns the item or
raises ``DropItem`` to stop further processing (standard Scrapy pattern).
"""

from __future__ import annotations

import logging

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from saral_scraper import normalize as nz

logger = logging.getLogger(__name__)


# ── 1. Clean ────────────────────────────────────────────────────────────────

class CleanPipeline:
    """Strip HTML, normalize whitespace, and derive typed/structured fields."""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Text fields
        for field in ("name", "ministry", "benefits", "eligibility",
                      "description", "state", "level", "apply_url", "source_url"):
            if field in adapter:
                adapter[field] = nz.clean_text(adapter.get(field))

        # List fields
        adapter["documents_required"] = nz.to_list(adapter.get("documents_required"))

        # Combined text used for keyword tagging + (later) embedding
        blob = " ".join(
            str(adapter.get(f) or "")
            for f in ("name", "benefits", "eligibility", "description", "ministry")
        )

        # Derive occupation / caste tags if the spider didn't set them
        if not adapter.get("target_occupation"):
            adapter["target_occupation"] = nz.detect_occupations(blob)
        else:
            adapter["target_occupation"] = nz.to_list(adapter.get("target_occupation"))

        if not adapter.get("caste_eligibility"):
            adapter["caste_eligibility"] = nz.detect_caste_eligibility(blob)
        else:
            adapter["caste_eligibility"] = nz.to_list(adapter.get("caste_eligibility"))

        # Parse income cap from eligibility text if not explicitly provided
        if adapter.get("income_limit") in (None, ""):
            adapter["income_limit"] = nz.parse_income(adapter.get("eligibility"))
        else:
            adapter["income_limit"] = nz.parse_income(str(adapter.get("income_limit")))

        # Parse age range from eligibility text if not explicitly provided
        if adapter.get("age_min") in (None, "") and adapter.get("age_max") in (None, ""):
            age_min, age_max = nz.parse_age_range(adapter.get("eligibility"))
            adapter["age_min"] = age_min
            adapter["age_max"] = age_max

        # Default level
        if not adapter.get("level"):
            adapter["level"] = "State" if adapter.get("state") else "Central"

        return item


# ── 2. Validate ─────────────────────────────────────────────────────────────

class ValidatePipeline:
    """Drop items missing the fields we need to make them useful."""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        name = adapter.get("name")
        if not name:
            raise DropItem("Missing scheme name")

        # Need *some* substantive content to embed/reason over.
        has_content = any(
            adapter.get(f) for f in ("eligibility", "benefits", "description")
        )
        if not has_content:
            raise DropItem(f"No eligibility/benefits/description for: {name}")

        return item


# ── 3. Duplicates (within a single crawl run) ───────────────────────────────

class DuplicatesPipeline:
    """Drop schemes already seen earlier in *this* crawl run."""

    def __init__(self):
        self.ids_seen: set[str] = set()

    def process_item(self, item, spider):
        from backend.app.models.scheme import make_scheme_id

        adapter = ItemAdapter(item)
        scheme_id = make_scheme_id(
            adapter.get("name", ""),
            level=adapter.get("level", "") or "",
            state=adapter.get("state", "") or "",
        )
        if scheme_id in self.ids_seen:
            raise DropItem(f"Duplicate scheme in run: {scheme_id}")
        self.ids_seen.add(scheme_id)
        return item


# ── 4. Pinecone (chunk → embed → idempotent upsert, incremental) ────────────

class PineconePipeline:
    """
    Convert the item to a canonical Scheme, skip it if unchanged since the
    last crawl (SQLite state), otherwise chunk + embed + upsert to Pinecone
    using deterministic vector ids.
    """

    def __init__(self, settings):
        self.index_name = settings.get("SARAL_PINECONE_INDEX")
        self.embed_model = settings.get("SARAL_EMBED_MODEL")
        self.chunk_size = settings.getint("SARAL_CHUNK_SIZE", 1000)
        self.chunk_overlap = settings.getint("SARAL_CHUNK_OVERLAP", 200)
        self.state_db = settings.get("SARAL_STATE_DB")
        self.dry_run = settings.getbool("SARAL_DRY_RUN", False)

        self.store = None
        self.vector_store = None
        self.splitter = None
        self.stats = {"new": 0, "changed": 0, "skipped": 0, "chunks": 0}

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def open_spider(self, spider):
        from saral_scraper.statestore import StateStore

        self.store = StateStore(self.state_db)

        from langchain_text_splitters import RecursiveCharacterTextSplitter

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        )

        if not self.dry_run:
            # Heavy imports only when we actually write.
            from langchain_huggingface import HuggingFaceEmbeddings
            from langchain_pinecone import PineconeVectorStore

            from backend.app.core.config import settings as backend_settings

            embeddings = HuggingFaceEmbeddings(model_name=self.embed_model)
            self.vector_store = PineconeVectorStore(
                index_name=self.index_name,
                embedding=embeddings,
                pinecone_api_key=backend_settings.PINECONE_API_KEY,
            )
            spider.logger.info(f"[Pinecone] Connected to index '{self.index_name}'")
        else:
            spider.logger.warning("[Pinecone] DRY RUN — not writing to Pinecone")

    def process_item(self, item, spider):
        from itemadapter import ItemAdapter
        from langchain_core.documents import Document

        from backend.app.models.scheme import Scheme, utc_now_iso, vector_id

        adapter = ItemAdapter(item)

        scheme = Scheme.new(
            name=adapter.get("name"),
            level=adapter.get("level") or "Central",
            state=(adapter.get("state") or None),
            ministry=adapter.get("ministry") or None,
            target_occupation=adapter.get("target_occupation") or [],
            caste_eligibility=adapter.get("caste_eligibility") or [],
            income_limit=adapter.get("income_limit"),
            age_min=adapter.get("age_min"),
            age_max=adapter.get("age_max"),
            benefits=adapter.get("benefits") or None,
            documents_required=adapter.get("documents_required") or [],
            apply_url=adapter.get("apply_url") or None,
            source_url=adapter.get("source_url") or None,
        )
        scheme.content_hash = scheme.compute_hash()

        # ── Incremental: skip unchanged schemes ──
        if not self.store.has_changed(scheme.scheme_id, scheme.content_hash):
            self.stats["skipped"] += 1
            raise DropItem(f"Unchanged since last crawl: {scheme.scheme_id}")

        is_new = self.store.get_hash(scheme.scheme_id) is None

        # ── Build the embedding text ──
        text_parts = [
            f"Scheme: {scheme.name}",
            f"Level: {scheme.level}" + (f" ({scheme.state})" if scheme.state else ""),
        ]
        if scheme.ministry:
            text_parts.append(f"Ministry: {scheme.ministry}")
        if adapter.get("eligibility"):
            text_parts.append(f"Eligibility: {adapter.get('eligibility')}")
        if scheme.benefits:
            text_parts.append(f"Benefits: {scheme.benefits}")
        if adapter.get("description"):
            text_parts.append(f"Details: {adapter.get('description')}")
        if scheme.documents_required:
            text_parts.append("Documents: " + ", ".join(scheme.documents_required))
        full_text = "\n".join(text_parts)

        metadata = scheme.to_metadata()
        chunks = self.splitter.split_text(full_text)

        if not self.dry_run and self.vector_store is not None:
            docs, ids = [], []
            for idx, chunk in enumerate(chunks):
                meta = dict(metadata)
                meta["chunk_index"] = idx
                docs.append(Document(page_content=chunk, metadata=meta))
                ids.append(vector_id(scheme.scheme_id, idx))
            self.vector_store.add_documents(documents=docs, ids=ids)

        # ── Record state so next crawl can skip if unchanged ──
        self.store.record(
            scheme.scheme_id,
            scheme.content_hash,
            last_seen=scheme.last_seen or utc_now_iso(),
            source_url=scheme.source_url or "",
            name=scheme.name,
        )

        self.stats["chunks"] += len(chunks)
        self.stats["new" if is_new else "changed"] += 1
        spider.logger.info(
            f"[{'NEW' if is_new else 'UPDATED'}] {scheme.scheme_id} "
            f"({len(chunks)} chunks)"
        )
        return item

    def close_spider(self, spider):
        total = self.store.count() if self.store else 0
        spider.logger.info(
            "[Pinecone] Crawl summary — "
            f"new={self.stats['new']} changed={self.stats['changed']} "
            f"skipped={self.stats['skipped']} chunks_upserted={self.stats['chunks']} "
            f"(tracked schemes total={total})"
        )
        if self.store:
            self.store.close()
