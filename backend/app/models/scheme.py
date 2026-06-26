"""
Canonical Scheme schema — the single source of truth.

This module is shared by:
  • the Scrapy ingestion service (Phase 1) — to emit structured items,
  • the PDF/JSON ingestion script — to tag chunks consistently,
  • the retrieval layer — to read/write Pinecone metadata.

It also exposes the deterministic ID + content-hash helpers that make
ingestion idempotent (re-ingesting the same scheme overwrites its vectors
instead of creating duplicates).
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

# ── Allowed values (kept loose on purpose; validation lives in pipelines) ──
LEVEL_CENTRAL = "Central"
LEVEL_STATE = "State"


# ── Deterministic ID / hashing helpers ────────────────────────────────────

def slugify(text: str) -> str:
    """Lowercase, ASCII-ish slug. 'Andhra Pradesh' -> 'andhra-pradesh'."""
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def make_scheme_id(name: str, level: str = "", state: str = "") -> str:
    """
    Build a stable, human-readable scheme_id from its identifying fields.

    The same scheme always maps to the same id, which is what gives the
    ingestion pipeline its idempotency.
    Example: ('PM-KISAN', 'Central', '') -> 'central-pm-kisan'
    """
    parts = [slugify(level), slugify(state), slugify(name)]
    base = "-".join(p for p in parts if p)
    return base or slugify(name) or "unknown-scheme"


def content_hash(text: str) -> str:
    """SHA-1 of arbitrary text — used to detect changed content."""
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()


def vector_id(scheme_id: str, chunk_index: int) -> str:
    """
    Deterministic Pinecone vector id for a given scheme chunk.

    id = sha1(f"{scheme_id}::{chunk_index}")

    Re-ingesting the same scheme produces identical ids, so Pinecone
    upserts (overwrites) the vectors rather than duplicating them.
    """
    return hashlib.sha1(f"{scheme_id}::{chunk_index}".encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    """Current UTC timestamp in ISO-8601 (used for last_seen)."""
    return datetime.now(timezone.utc).isoformat()


# ── Canonical record ───────────────────────────────────────────────────────

class Scheme(BaseModel):
    """A single government scheme, normalized across all data sources."""

    scheme_id: str
    name: str
    level: str = LEVEL_CENTRAL                      # "Central" | "State"
    state: Optional[str] = None                     # None/"" for Central
    ministry: Optional[str] = None

    target_occupation: list[str] = Field(default_factory=list)
    caste_eligibility: list[str] = Field(default_factory=list)
    income_limit: Optional[int] = None              # annual ₹ cap, None = no cap
    age_min: Optional[int] = None
    age_max: Optional[int] = None

    benefits: Optional[str] = None
    documents_required: list[str] = Field(default_factory=list)

    apply_url: Optional[str] = None
    source_url: Optional[str] = None

    last_seen: Optional[str] = None                 # ISO-8601 timestamp
    content_hash: Optional[str] = None

    # ── Convenience constructors / serializers ──

    @classmethod
    def new(
        cls,
        name: str,
        level: str = LEVEL_CENTRAL,
        state: Optional[str] = None,
        **kwargs,
    ) -> "Scheme":
        """Create a Scheme with a derived scheme_id and last_seen filled in."""
        scheme_id = make_scheme_id(name, level=level, state=state or "")
        return cls(
            scheme_id=scheme_id,
            name=name,
            level=level,
            state=state,
            last_seen=kwargs.pop("last_seen", utc_now_iso()),
            **kwargs,
        )

    def compute_hash(self) -> str:
        """Stable hash over the meaningful content fields (for change detection)."""
        payload = "|".join(
            str(v) for v in (
                self.name, self.level, self.state, self.ministry,
                sorted(self.target_occupation), sorted(self.caste_eligibility),
                self.income_limit, self.age_min, self.age_max,
                self.benefits, sorted(self.documents_required),
                self.apply_url,
            )
        )
        return content_hash(payload)

    def to_metadata(self) -> dict:
        """
        Flatten to a Pinecone-safe metadata dict.

        Pinecone metadata accepts str / number / bool / list[str], so we
        drop None values and keep lists as lists of strings.
        """
        meta = {
            "scheme_id": self.scheme_id,
            "name": self.name,
            "level": self.level,
            "state": self.state or "",
            "ministry": self.ministry or "",
            "target_occupation": self.target_occupation,
            "caste_eligibility": self.caste_eligibility,
            "documents_required": self.documents_required,
            "apply_url": self.apply_url or "",
            "source_url": self.source_url or "",
            "last_seen": self.last_seen or "",
            "content_hash": self.content_hash or self.compute_hash(),
        }
        if self.income_limit is not None:
            meta["income_limit"] = self.income_limit
        if self.age_min is not None:
            meta["age_min"] = self.age_min
        if self.age_max is not None:
            meta["age_max"] = self.age_max
        # Strip empty strings to keep metadata lean
        return {k: v for k, v in meta.items() if v not in ("", None)}
