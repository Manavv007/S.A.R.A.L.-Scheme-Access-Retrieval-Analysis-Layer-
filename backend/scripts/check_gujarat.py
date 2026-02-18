"""
Standalone script to debug Gujarat-specific scheme retrieval.
Usage: python -m backend.scripts.check_gujarat
"""

import sys
import os
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from backend.app.core.config import settings

def check_gujarat():
    print(f"🕵️‍♂️ Checking for Gujarat Documents in Index: {settings.PINECONE_INDEX_NAME}")
    
    # We use HuggingFace embeddings as per project config (not OpenAI)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    vector_store = PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=embeddings,
        pinecone_api_key=settings.PINECONE_API_KEY
    )

    # 1. Search for generic Gujarat keyword
    query = "Gujarat government schemes welfare"
    print(f"\n🔍 Searching for: '{query}'")
    
    try:
        results = vector_store.similarity_search_with_score(query, k=10)
    except Exception as e:
        print(f"❌ Error during search: {e}")
        return

    if not results:
        print("⚠️ No results found! The index might NOT contain Gujarat schemes.")
        return

    print(f"✅ Found {len(results)} potential matches:\n")
    for i, (doc, score) in enumerate(results):
        state = doc.metadata.get("state", "UNKNOWN")
        source = doc.metadata.get("source", "UNKNOWN")
        content_snippet = doc.page_content[:150].replace('\n', ' ')
        
        print(f"   [{i+1}] Score: {score:.4f} | State: '{state}'")
        print(f"       Source: {source}")
        print(f"       Snippet: {content_snippet}...\n")

if __name__ == "__main__":
    check_gujarat()
