"""
API client – sends chat queries and profile data to the FastAPI backend.
"""

import requests

import os
import requests

# Check if we are running in Cloud Deployment Mode (Monolithic)
DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "LOCAL")

if DEPLOYMENT_ENV == "CLOUD":
    # Import backend services directly
    try:
        from backend.app.services.rag_retriever import RAGService
        from backend.app.services.llm_engine import LLMEngine
        from backend.app.services.recommendation import RecommendationService
        from backend.app.models.dtos import UserProfile
    except ImportError as e:
        print(f"❌ Deploy Error: Could not import backend services. {e}")

BASE_URL = "http://localhost:8000/api/v1"


def get_chat_response(query: str, profile: dict | None = None, history: list | None = None):
    """Send a query to the backend chat endpoint and return the JSON response."""
    
    # ── CLOUD MODE: Direct Function Call ─────────────────
    if DEPLOYMENT_ENV == "CLOUD":
        try:
            rag = RAGService()
            llm = LLMEngine()

            # Extract language
            language = "English"
            if profile and "language" in profile:
                language = profile["language"]

            context = rag.get_context(query)
            answer = llm.generate_answer(
                query,
                context,
                language=language,
                history=history or [],
            )
            return {"answer": answer, "source_docs": [context]}
        except Exception as e:
            print(f"Cloud Chat Error: {e}")
            return None

    # ── LOCAL MODE: HTTP Request ─────────────────────────
    try:
        payload = {"query": query}
        if profile:
            payload["profile"] = profile
        if history:
            payload["history"] = history
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def get_recommendations(profile: dict):
    """Send a user profile to the recommend endpoint and return the result."""
    
    # ── CLOUD MODE: Direct Function Call ─────────────────
    if DEPLOYMENT_ENV == "CLOUD":
        try:
            # Convert dict to Pydantic model
            user_profile = UserProfile(**profile)
            service = RecommendationService()
            results = service.get_eligible_schemes(user_profile)
            return {"recommendations": results}
        except Exception as e:
            print(f"Cloud Recs Error: {e}")
            return None

    # ── LOCAL MODE: HTTP Request ─────────────────────────
    try:
        response = requests.post(f"{BASE_URL}/recommend", json=profile)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None
