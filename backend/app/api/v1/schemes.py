"""
Schemes API router – personalised scheme recommendations.
"""

import traceback

from fastapi import APIRouter

from backend.app.models.dtos import UserProfile
from backend.app.services.recommendation import RecommendationService

router = APIRouter()


@router.post("/recommend")
async def recommend(profile: UserProfile):
    """Receive a user profile and return eligible scheme recommendations."""
    try:
        print(f"DEBUG API: Received profile {profile}")
        service = RecommendationService()
        results = service.get_eligible_schemes(profile)
        print(f"DEBUG API: Returning {len(results)} schemes")
        return {"recommendations": results}
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"API CRASH: {error_msg}")
        return {"error": str(e), "details": error_msg}
