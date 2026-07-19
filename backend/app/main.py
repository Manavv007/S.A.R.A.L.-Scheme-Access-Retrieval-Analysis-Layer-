"""
FastAPI application entry point for BharatScheme-AI (S.A.R.A.L.).

This is the real integration surface for every frontend (Streamlit today,
Next.js in Phase 3). Frontends call it over HTTP - there is no in-process
"monolithic" import path anymore.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.schemes import router as schemes_router
from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.voice import router as voice_router
from backend.app.core.logging_config import setup_logging
from backend.app.core.security import RateLimitMiddleware

setup_logging()

app = FastAPI(title="S.A.R.A.L. API")

# Rate limiting (per-IP fixed window; SARAL_RATE_LIMIT req/min, 0 disables).
app.add_middleware(RateLimitMiddleware)

# CORS - allow the configured frontend origins. Defaults cover local dev for
# both Streamlit (8501) and Next.js (3000). Override with SARAL_CORS_ORIGINS
# (comma-separated) in production.
_default_origins = "http://localhost:3000,http://localhost:8501"
_origins = [
    o.strip()
    for o in os.getenv("SARAL_CORS_ORIGINS", _default_origins).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/v1")
app.include_router(schemes_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"status": "online"}


if __name__ == "__main__":
    # Auto-reload in dev when SARAL_RELOAD=1 (picks up code changes without a
    # manual restart). Reload requires the import-string form of the app.
    if os.getenv("SARAL_RELOAD", "0") == "1":
        uvicorn.run(
            "backend.app.main:app", host="0.0.0.0", port=8000, reload=True
        )
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)
