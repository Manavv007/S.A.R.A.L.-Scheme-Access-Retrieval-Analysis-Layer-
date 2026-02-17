"""
Chat API router – handles user queries via the RAG + LLM pipeline.
"""

from fastapi import APIRouter, HTTPException

from backend.app.models.dtos import ChatRequest, ChatResponse
from backend.app.services.rag_retriever import RAGService
from backend.app.services.llm_engine import LLMEngine

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Accept a user query, retrieve context, and return an LLM answer."""
    try:
        rag = RAGService()
        llm = LLMEngine()

        # Extract language from profile if available
        language = "English"
        if request.profile and request.profile.language:
            language = request.profile.language

        context = rag.get_context(request.query)
        answer = llm.generate_answer(
            request.query,
            context,
            language=language,
            history=request.history,
        )

        return ChatResponse(answer=answer, source_docs=[context])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
