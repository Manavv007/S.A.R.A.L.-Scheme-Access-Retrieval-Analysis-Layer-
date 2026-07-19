"""
Shared service singletons.

The heavy objects — the ``all-MiniLM-L6-v2`` embedding model, the Pinecone
vector store, and the Groq client — are expensive to construct (the embedding
model in particular reloads its weights each time). Building them per request
was the dominant source of ``/recommend`` latency.

These accessors build each service **once per process** and hand back the same
instance on every call, so warm requests never pay the load cost again. Import
these instead of constructing the services directly in request handlers.
"""

from functools import lru_cache

from backend.app.services.llm_engine import LLMEngine
from backend.app.services.rag_retriever import RAGService
from backend.app.services.recommendation import RecommendationService


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    """Process-wide singleton RAG retriever (loads MiniLM + Pinecone once)."""
    return RAGService()


@lru_cache(maxsize=1)
def get_llm_engine() -> LLMEngine:
    """Process-wide singleton Groq LLM engine."""
    return LLMEngine()


@lru_cache(maxsize=1)
def get_recommendation_service() -> RecommendationService:
    """
    Process-wide singleton recommendation service, wired to the shared RAG and
    LLM singletons so nothing is reloaded per request.
    """
    return RecommendationService(
        rag_service=get_rag_service(),
        llm_engine=get_llm_engine(),
    )


@lru_cache(maxsize=1)
def get_groq_client():
    """Process-wide singleton raw Groq client (used for Whisper STT)."""
    from groq import Groq

    from backend.app.core.config import settings

    return Groq(api_key=settings.GROQ_API_KEY)


@lru_cache(maxsize=1)
def get_conversation_engine():
    """
    Process-wide singleton dialogue manager for the live voice conversation.

    Imported lazily to avoid a circular import (conversation.py imports the
    LLM/recommendation singletons from this module).
    """
    from backend.app.services.conversation import ConversationEngine

    return ConversationEngine()
