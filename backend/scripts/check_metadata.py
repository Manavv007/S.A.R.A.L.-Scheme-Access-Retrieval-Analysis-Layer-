import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from backend.app.core.config import settings

def check_index_stats():
    print("Connecting to Pinecone...")

    embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
    vector_store = PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=embeddings,
        pinecone_api_key=settings.PINECONE_API_KEY
    )

    # 1. Perform a generic search (Search for "scheme")
    print("\nSearching for 'scheme' to inspect metadata...")
    results = vector_store.similarity_search("farming scheme", k=5)

    if not results:
        print("No documents found! Your database might be empty.")
        return

    # 2. Print the Metadata of what we found
    print(f"\nFound {len(results)} documents. Inspecting Tags:\n")
    for i, doc in enumerate(results):
        meta = doc.metadata
        print(f"Doc {i+1}: {meta.get('source_file', 'Unknown File')}")
        print(f"    State Tag: '{meta.get('state', 'MISSING')}'")
        print(f"   --------------------------------------------------")

if __name__ == "__main__":
    check_index_stats()
