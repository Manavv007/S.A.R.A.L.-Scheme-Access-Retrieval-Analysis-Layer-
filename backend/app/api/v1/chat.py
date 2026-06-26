"""
Chat API router - handles user queries via the RAG + LLM pipeline.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.models.dtos import ChatRequest, ChatResponse
from backend.app.services.rag_retriever import RAGService
from backend.app.services.llm_engine import LLMEngine

router = APIRouter()


def _language_of(request: ChatRequest) -> str:
    if request.profile and request.profile.language:
        return request.profile.language
    return "English"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Accept a user query, retrieve context, and return an LLM answer."""
    try:
        rag = RAGService()
        llm = LLMEngine()

        context = rag.get_context(request.query)
        answer = llm.generate_answer(
            request.query,
            context,
            language=_language_of(request),
            history=request.history,
        )

        return ChatResponse(answer=answer, source_docs=[context])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream the LLM answer token-by-token as plain text."""
    rag = RAGService()
    llm = LLMEngine()
    context = rag.get_context(request.query)
    language = _language_of(request)

    def token_generator():
        try:
            for token in llm.generate_answer_stream(
                request.query,
                context,
                language=language,
                history=request.history,
            ):
                yield token
        except Exception as e:
            yield f"\n[Error: {e}]"

    return StreamingResponse(
        token_generator(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
