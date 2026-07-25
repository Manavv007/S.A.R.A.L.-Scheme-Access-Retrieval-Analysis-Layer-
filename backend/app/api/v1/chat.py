"""
Chat API router - handles user queries via the RAG + LLM pipeline.

Intent-based retrieval:
  profile_only → skip Pinecone; answer from the eligibility form
  schemes/both → retrieve scheme docs, then answer with form + docs
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.models.dtos import ChatRequest, ChatResponse
from backend.app.services.providers import get_llm_engine, get_rag_service
from backend.app.core.security import require_api_key

router = APIRouter(dependencies=[Depends(require_api_key)])


def _language_of(request: ChatRequest) -> str:
    if request.profile and request.profile.language:
        return request.profile.language
    return "English"


def _profile_dict(request: ChatRequest) -> dict | None:
    return request.profile.model_dump() if request.profile else None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Accept a user query, retrieve context if needed, and return an LLM answer."""
    try:
        llm = get_llm_engine()
        profile = _profile_dict(request)
        intent = llm.classify_intent(
            request.query, profile=profile, history=request.history
        )

        context = ""
        if intent in ("schemes", "both"):
            context = get_rag_service().get_context(request.query)

        answer = llm.generate_answer(
            request.query,
            context=context,
            language=_language_of(request),
            history=request.history,
            profile=profile,
            intent=intent,
        )
        return ChatResponse(
            answer=answer,
            source_docs=[context] if context else [],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream the LLM answer token-by-token as plain text."""
    llm = get_llm_engine()
    profile = _profile_dict(request)
    language = _language_of(request)
    intent = llm.classify_intent(
        request.query, profile=profile, history=request.history
    )

    context = ""
    if intent in ("schemes", "both"):
        context = get_rag_service().get_context(request.query)

    def token_generator():
        try:
            for token in llm.generate_answer_stream(
                request.query,
                context=context,
                language=language,
                history=request.history,
                profile=profile,
                intent=intent,
            ):
                yield token
        except Exception as e:
            yield f"\n[Error: {e}]"

    return StreamingResponse(
        token_generator(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
