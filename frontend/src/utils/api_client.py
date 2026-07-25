"""
API client – sends chat queries and profile data to the FastAPI backend.

The frontend talks to the backend over HTTP only. The backend base URL is
configurable via the ``SARAL_API_BASE_URL`` (or ``BACKEND_URL``) environment
variable so the same client works for local dev and separate-host deployments.
"""

import os

import requests

# Real integration surface: the FastAPI service. Override per environment.
BASE_URL = (
    os.getenv("SARAL_API_BASE_URL")
    or os.getenv("BACKEND_URL")
    or "http://localhost:8000/api/v1"
).rstrip("/")

# Network timeout (seconds) for backend calls.
REQUEST_TIMEOUT = float(os.getenv("SARAL_API_TIMEOUT", "120"))


def _auth_headers() -> dict:
    """Forward SARAL_API_KEY when backend auth is enabled."""
    key = os.getenv("SARAL_API_KEY")
    return {"X-API-Key": key} if key else {}


def get_chat_response(query: str, profile: dict | None = None, history: list | None = None):
    """
    Send a query to the backend chat endpoint.
    Returns: (json_response | None, debug_info_dict)
    """
    url = f"{BASE_URL}/chat"
    payload: dict = {"query": query}
    if profile:
        payload["profile"] = profile
    if history:
        payload["history"] = history

    debug_info = {
        "url": url,
        "payload": payload,
        "status_code": None,
        "response_text": None,
        "error": None,
    }

    try:
        response = requests.post(
            url, json=payload, headers=_auth_headers(), timeout=REQUEST_TIMEOUT
        )
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
    Returns: (json_response | None, debug_info_dict)
    """
    url = f"{BASE_URL}/recommend"
    debug_info = {
        "url": url,
        "payload": profile,
        "status_code": None,
        "response_text": None,
        "error": None,
    }

    try:
        response = requests.post(
            url, json=profile, headers=_auth_headers(), timeout=REQUEST_TIMEOUT
        )
        debug_info["status_code"] = response.status_code
        debug_info["response_text"] = response.text

        response.raise_for_status()
        return response.json(), debug_info
    except Exception as e:
        debug_info["error"] = str(e)
        return None, debug_info
