"""
Document Ingestion Script
========================
Recursively loads PDFs, CSVs, JSONs, and TXT files from data/raw_pdfs/,
splits them into chunks, and upserts each file's chunks to Pinecone
immediately (file-by-file batch processing).

Ingestion is idempotent: every chunk is written with a deterministic
vector id (sha1("{scheme_id}::{chunk_index}")), so re-running the script
overwrites the existing vectors for a scheme instead of creating
duplicates.

Usage (from project root):
    python -m backend.scripts.ingest_pdfs
"""

import os

from tqdm import tqdm
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

from backend.app.core.config import settings
from backend.app.models.scheme import (
    content_hash,
    make_scheme_id,
    utc_now_iso,
    vector_id,
)

# Ensure Pinecone SDK can find the API key via env variable
os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY

DATA_DIR = os.path.join(os.getcwd(), "data", "raw_pdfs")
SUPPORTED_EXT = (".pdf", ".csv", ".json", ".txt")


def _get_loader(file_path: str):
    """Return the appropriate document loader for the given file."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return PyPDFLoader(file_path)
    if ext == ".csv":
        return CSVLoader(file_path, encoding="utf-8")
    if ext in (".json", ".txt"):
        return TextLoader(file_path, encoding="utf-8")
    return None


def ingest_docs() -> None:
    """Load, chunk, and upsert documents file-by-file with progress tracking."""

    data_dir = os.path.abspath(DATA_DIR)

    if not os.path.isdir(data_dir):
        print(f"[WARN] Directory not found: {data_dir}")
        print("       Please create data/raw_pdfs/ and add your files there.")
        return

    # 1. Discover all supported files recursively
    file_list = []
    for root, _dirs, files in os.walk(data_dir):
        for fname in files:
            if fname.lower().endswith(SUPPORTED_EXT):
                file_list.append(os.path.join(root, fname))

    if not file_list:
        print(f"[WARN] No supported files found in {data_dir}")
        return

    print(f"[INFO] Found {len(file_list)} file(s) across all sub-folders.\n")

    # 2. Initialize shared resources (once)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    print("[INIT] Loading embedding model (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Connect to the index once and reuse it for every file. Upserting with
    # deterministic ids makes re-ingestion idempotent (overwrite, not duplicate).
    vector_store = PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=embeddings,
        pinecone_api_key=settings.PINECONE_API_KEY,
    )

    total_chunks = 0
    skipped = 0

    # 3. Process each file: load → tag → chunk → upload
    for file_path in tqdm(file_list, desc="Ingesting files", unit="file"):
        fname = os.path.basename(file_path)
        tqdm.write(f"  Processing: {fname}")

        # Smart tagging: subfolder name = state, root = Central
        parent_folder = os.path.basename(os.path.dirname(file_path))
        state = parent_folder if parent_folder != os.path.basename(data_dir) else "Central"

        # Stable scheme_id derived from the source file (one "scheme" per file
        # at the PDF stage; the Scrapy service in Phase 1 will emit finer ids).
        level = "State" if state != "Central" else "Central"
        scheme_state = "" if state == "Central" else state
        scheme_name = os.path.splitext(fname)[0]
        scheme_id = make_scheme_id(scheme_name, level=level, state=scheme_state)
        ingested_at = utc_now_iso()

        loader = _get_loader(file_path)
        if loader is None:
            continue

        # Load documents
        try:
            docs = loader.load()
        except Exception as e:
            tqdm.write(f"  [SKIP] {fname}: {e}")
            skipped += 1
            continue

        # Inject metadata
        for doc in docs:
            doc.metadata["state"] = state
            doc.metadata["source_file"] = fname
            doc.metadata["scheme_id"] = scheme_id
            doc.metadata["level"] = level

        # Chunk
        chunks = splitter.split_documents(docs)
        if not chunks:
            continue

        # Deterministic ids + per-chunk content hash → idempotent upsert.
        ids = []
        for idx, chunk in enumerate(chunks):
            ids.append(vector_id(scheme_id, idx))
            chunk.metadata["chunk_index"] = idx
            chunk.metadata["content_hash"] = content_hash(chunk.page_content)
            chunk.metadata["last_seen"] = ingested_at

        # Upsert immediately (same ids overwrite instead of duplicating)
        try:
            vector_store.add_documents(documents=chunks, ids=ids)
            total_chunks += len(chunks)
        except Exception as e:
            tqdm.write(f"  [UPLOAD FAIL] {fname}: {e}")
            skipped += 1

    print(f"\n[DONE] Ingested {total_chunks} chunks from {len(file_list) - skipped} files.")
    if skipped:
        print(f"[WARN] Skipped {skipped} file(s) due to errors.")


if __name__ == "__main__":
    ingest_docs()
