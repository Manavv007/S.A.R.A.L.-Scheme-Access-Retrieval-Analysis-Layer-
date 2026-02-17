"""
API client – sends chat queries and profile data to the FastAPI backend.
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"


def get_chat_response(query: str, profile: dict | None = None, history: list | None = None):
    """Send a query to the backend chat endpoint and return the JSON response."""
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
    try:
        response = requests.post(f"{BASE_URL}/recommend", json=profile)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None
