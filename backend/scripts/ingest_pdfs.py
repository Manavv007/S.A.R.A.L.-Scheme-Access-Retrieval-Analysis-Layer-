"""
Document Ingestion Script
========================
Recursively loads PDFs, CSVs, JSONs, and TXT files from data/raw_pdfs/,
splits them into chunks, and upserts each file's chunks to Pinecone
immediately (file-by-file batch processing).

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

    total_chunks = 0
    skipped = 0

    # 3. Process each file: load → tag → chunk → upload
    for file_path in tqdm(file_list, desc="Ingesting files", unit="file"):
        fname = os.path.basename(file_path)
        tqdm.write(f"  📄 Processing: {fname}")

        # Smart tagging: subfolder name = state, root = Central
        parent_folder = os.path.basename(os.path.dirname(file_path))
        state = parent_folder if parent_folder != os.path.basename(data_dir) else "Central"

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

        # Chunk
        chunks = splitter.split_documents(docs)
        if not chunks:
            continue

        # Upload immediately
        try:
            PineconeVectorStore.from_documents(
                documents=chunks,
                embedding=embeddings,
                index_name=settings.PINECONE_INDEX_NAME,
            )
            total_chunks += len(chunks)
        except Exception as e:
            tqdm.write(f"  [UPLOAD FAIL] {fname}: {e}")
            skipped += 1

    print(f"\n[DONE] Ingested {total_chunks} chunks from {len(file_list) - skipped} files.")
    if skipped:
        print(f"[WARN] Skipped {skipped} file(s) due to errors.")


if __name__ == "__main__":
    ingest_docs()
