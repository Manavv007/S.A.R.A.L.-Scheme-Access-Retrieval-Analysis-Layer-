"""
Schemes API router - personalised scheme recommendations.
"""

import json
import traceback

from fastapi import APIRouter, Depends

from backend.app.core.cache import cache
from backend.app.core.logging_config import get_logger
from backend.app.core.security import require_api_key
from backend.app.models.dtos import UserProfile
from backend.app.services.recommendation import RecommendationService

logger = get_logger("api.schemes")

router = APIRouter(dependencies=[Depends(require_api_key)])

# Cache recommendations for identical profiles to cut LLM cost/latency.
_RECOMMEND_TTL = 3600  # 1 hour


@router.post("/recommend")
async def recommend(profile: UserProfile):
    """Receive a user profile and return eligible scheme recommendations."""
    try:
        key = cache.make_key("recommend", profile.model_dump())
        cached = cache.get(key)
        if cached is not None:
            logger.info(f"cache hit key={key}")
            return {"recommendations": json.loads(cached), "cached": True}

        logger.info(f"recommend profile occupation={profile.occupation} state={profile.state}")
        service = RecommendationService()
        results = service.get_eligible_schemes(profile)

        cache.set(key, json.dumps(results), ttl=_RECOMMEND_TTL)
        return {"recommendations": results, "cached": False}
    except Exception as e:
        logger.error(f"recommend failed: {e}")
        return {"error": str(e), "details": traceback.format_exc()}
