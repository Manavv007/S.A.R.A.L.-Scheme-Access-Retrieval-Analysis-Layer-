"""
API client – sends chat queries and profile data to the FastAPI backend.
"""

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
    """
    Send a query to the backend chat endpoint.
    Returns: (json_response, debug_info_dict)
    """
    url = f"{BASE_URL}/chat"
    payload = {"query": query}
    if profile:
        payload["profile"] = profile
    if history:
        payload["history"] = history
    
    debug_info = {
        "url": url,
        "payload": payload,
        "deployment_env": DEPLOYMENT_ENV,
        "status_code": None,
        "response_text": None,
        "error": None
    }

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
            
            response_data = {"answer": answer, "source_docs": [context]}
            debug_info["status_code"] = 200
            debug_info["response_text"] = "Generated internally via LLMEngine"
            return response_data, debug_info

        except Exception as e:
            debug_info["error"] = f"Cloud Internal Error: {str(e)}"
            return None, debug_info

    # ── LOCAL MODE: HTTP Request ─────────────────────────
    try:
        response = requests.post(url, json=payload)
        debug_info["status_code"] = response.status_code
        debug_info["response_text"] = response.text
        
        response.raise_for_status()
        return response.json(), debug_info
    except Exception as e:
        debug_info["error"] = str(e)
        return None, debug_info


def get_recommendations(profile: dict):
    """
    Send a user profile to the recommend endpoint.
    Returns: (json_response, debug_info_dict)
    """
    url = f"{BASE_URL}/recommend"
    debug_info = {
        "url": url,
        "payload": profile,
        "deployment_env": DEPLOYMENT_ENV,
        "status_code": None,
        "response_text": None,
        "error": None
    }

    # ── CLOUD MODE: Direct Function Call ─────────────────
    if DEPLOYMENT_ENV == "CLOUD":
        try:
            # Convert dict to Pydantic model
            user_profile = UserProfile(**profile)
            service = RecommendationService()
            results = service.get_eligible_schemes(user_profile)
            
            response_data = {"recommendations": results}
            debug_info["status_code"] = 200
            debug_info["response_text"] = f"Found {len(results)} schemes internally"
            return response_data, debug_info

        except Exception as e:
            debug_info["error"] = f"Cloud Internal Error: {str(e)}"
            return None, debug_info

    # ── LOCAL MODE: HTTP Request ─────────────────────────
    try:
        response = requests.post(url, json=profile)
        debug_info["status_code"] = response.status_code
        debug_info["response_text"] = response.text
        
        response.raise_for_status()
        return response.json(), debug_info
    except Exception as e:
        debug_info["error"] = str(e)
        return None, debug_info
