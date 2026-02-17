from backend.app.services.rag_retriever import RAGService
from backend.app.services.llm_engine import LLMEngine
import time

def test_advisor():
    print("🚀 Initializing BharatScheme-AI...")
    rag = RAGService()
    llm = LLMEngine()

    # Query matching your uploaded PDF
    query = "What is the eligibility for this scheme?"
    
    print(f"\n❓ User Question: {query}")
    print("..." * 10)

    # 1. RETRIEVE
    start = time.time()
    context = rag.get_context(query)
    print(f"📚 Retrieved Context in {time.time() - start:.2f}s")

    # 2. GENERATE
    start = time.time()
    print("🧠 Thinking (Groq Llama-3)...")
    answer = llm.generate_answer(query, context)
    
    print("\n" + "="*40)
    print("💡 AI ADVISOR ANSWER:")
    print("="*40)
    print(answer)
    print("="*40)
    print(f"✨ Generated in {time.time() - start:.2f}s")

if __name__ == "__main__":
    test_advisor()
