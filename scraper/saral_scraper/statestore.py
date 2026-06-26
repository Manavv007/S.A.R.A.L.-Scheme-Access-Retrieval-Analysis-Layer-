"""
SQLite-backed crawl state for incremental ingestion.

Tracks, per scheme:  scheme_id -> (content_hash, last_seen)

On each crawl the PineconePipeline asks `has_changed(scheme_id, hash)`:
  • unchanged  -> the item is skipped (no re-embed, no Pinecone write)
  • new/changed-> the item is (re)embedded + upserted, then `record(...)`

This keeps embedding compute and Pinecone write volume proportional to what
actually changed, which matters once the scheduled crawler runs regularly.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Optional


class StateStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schemes (
                scheme_id    TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                last_seen    TEXT,
                source_url   TEXT,
                name         TEXT
            )
            """
        )
        self._conn.commit()

    # ── Reads ──
    def get_hash(self, scheme_id: str) -> Optional[str]:
        cur = self._conn.execute(
            "SELECT content_hash FROM schemes WHERE scheme_id = ?", (scheme_id,)
        )
        row = cur.fetchone()
        return row[0] if row else None

    def has_changed(self, scheme_id: str, content_hash: str) -> bool:
        """True if the scheme is new or its content hash differs from stored."""
        return self.get_hash(scheme_id) != content_hash

    # ── Writes ──
    def record(
        self,
        scheme_id: str,
        content_hash: str,
        last_seen: str,
        source_url: str = "",
        name: str = "",
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO schemes (scheme_id, content_hash, last_seen, source_url, name)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(scheme_id) DO UPDATE SET
                content_hash = excluded.content_hash,
                last_seen    = excluded.last_seen,
                source_url   = excluded.source_url,
                name         = excluded.name
            """,
            (scheme_id, content_hash, last_seen, source_url, name),
        )
        self._conn.commit()

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM schemes")
        return cur.fetchone()[0]

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass
