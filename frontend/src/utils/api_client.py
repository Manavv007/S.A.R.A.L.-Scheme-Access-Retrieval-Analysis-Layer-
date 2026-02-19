"""
API client – sends chat queries and profile data to the FastAPI backend.
"""

import requests



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
        "status_code": None,
        "response_text": None,
        "error": None
    }

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
        "status_code": None,
        "response_text": None,
        "error": None
    }

    try:
        response = requests.post(url, json=profile)
        debug_info["status_code"] = response.status_code
        debug_info["response_text"] = response.text
        
        response.raise_for_status()
        return response.json(), debug_info
    except Exception as e:
        debug_info["error"] = str(e)
        return None, debug_info
