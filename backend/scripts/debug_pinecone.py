"""
Standalone RAG Diagnostic Script to debug Pinecone retrieval issues.
Usage: python -m backend.scripts.debug_pinecone
"""

import time
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from backend.app.core.config import settings

def main():
    print("Initializing Diagnostic Script...")
    print(f"   Index Name: {settings.PINECONE_INDEX_NAME}")
    print(f"   API Key: {settings.PINECONE_API_KEY[:5]}... (masked)")

    # 1. Initialize Pinecone
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=embeddings,
        pinecone_api_key=settings.PINECONE_API_KEY,
    )

    # 2. Test 1: Raw Dump (Check if index is empty)
    print("\nTEST 1: Raw Dump (First 10 vectors via dummy search)")
    try:
        # Searching for "." or common words often brings back random docs
        results = vector_store.similarity_search_with_score(".", k=10)
        if not results:
            print("   Index appears EMPTY! No results found for dummy query.")
        else:
            print(f"   Found {len(results)} vectors.")
            for i, (doc, score) in enumerate(results):
                meta = doc.metadata
                print(f"   [{i+1}] Score: {score:.4f} | State: {meta.get('state', 'N/A')} | Occupation: {meta.get('occupation', 'N/A')}")
    except Exception as e:
        print(f"   Error connecting to Pinecone: {e}")
        return

    # 3. Test 2: Targeted Search
    query = "scholarship for students in andhra pradesh"
    print(f"\nTEST 2: Targeted Search ('{query}')")
    results = vector_store.similarity_search_with_score(query, k=10)

    if not results:
        print("   No results found for targeted query.")
    else:
        for i, (doc, score) in enumerate(results):
            meta = doc.metadata
            content_preview = doc.page_content[:100].replace('\n', ' ')
            print(f"   [{i+1}] Score: {score:.4f} | State: {meta.get('state', 'N/A')} | Occupation: {meta.get('occupation', 'N/A')}")
            print(f"       Content: {content_preview}...")

    # 4. Test 3: Keyword Search
    keyword_query = "National Means-cum-Merit Scholarship"
    print(f"\nTEST 3: Keyword Matches for '{keyword_query}'")
    results = vector_store.similarity_search_with_score(keyword_query, k=5)

    if not results:
        print("   No results found for keyword query.")
    else:
        for i, (doc, score) in enumerate(results):
            meta = doc.metadata
            print(f"   [{i+1}] Score: {score:.4f} | Source: {meta.get('source', 'Unknown')}")
            print(f"       Metadata: {meta}")

    print("\nDiagnostic Complete.")

if __name__ == "__main__":
    main()
