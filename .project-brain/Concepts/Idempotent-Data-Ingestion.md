---
type: concept
project: S.A.R.A.L.
status: active
confidence: confirmed
created: 2026-07-05
related:
  - "[[Ingestion-Scraper]]"
  - "[[RAG-Retrieval-Augmented-Generation]]"
---

# Idempotent Data Ingestion

## 1. What is Idempotent Ingestion?
Idempotent Data Ingestion is the database synchronization pattern built into S.A.R.A.L.'s crawlers and ingestion scripts ([pipelines.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/scraper/saral_scraper/pipelines.py)). It ensures that re-running spiders does not create duplicate vector chunks in Pinecone or corrupt existing scheme entries.

---

## 2. Ingestion Rules & Flow
1. **Deterministic Vector IDs:** Instead of generating random hashes, S.A.R.A.L. generates vector IDs based on:
   * `sha1(f"{scheme_id}::{chunk_index}")`
   * Where `scheme_id` is derived from the scheme name, level, and state residency.
2. **SQLite Content Hash Cache:** Spiders record scheme hashes in a local `crawl_state.sqlite` SQLite database.
3. **Difference Detection:** During crawler executions, the pipeline checks:
   * If the `scheme_id` does not exist in SQLite, the scheme is processed as **NEW**.
   * If it exists but the hash differs, it is processed as **UPDATED** (upserting to Pinecone overwrites matching IDs).
   * If the hash matches, it is **SKIPPED** (`DropItem`), preventing unnecessary API calls.

---

## 3. Why It Matters
Frequent scraping updates can result in duplicate index entries, increasing search latency and LLM billing costs. Idempotency guarantees vector store consistency, allowing developers to run spiders daily or weekly without manual database resets.
