from backend.app.services.rag_retriever import RAGService

def test_retrieval():
    print("🤖 Waking up the Librarian...")
    service = RAGService()
    
    # Change this query to match whatever PDF you uploaded!
    query = "Who is eligible for the scheme?" 
    
    print(f"🔍 Searching for: '{query}'")
    context = service.get_context(query)
    
    print("\n📄 FOUND CONTEXT:\n" + "="*40)
    print(context[:500] + "...") # Print first 500 chars
    print("="*40)

if __name__ == "__main__":
    test_retrieval()
