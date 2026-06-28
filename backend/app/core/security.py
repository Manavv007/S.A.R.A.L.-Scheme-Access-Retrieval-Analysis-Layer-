"""
Security hardening for the S.A.R.A.L. backend.

* API-key auth — opt-in. When ``SARAL_API_KEY`` is set, every protected route
  requires a matching ``X-API-Key`` header; when unset, auth is disabled (dev).
* Rate limiting — a simple in-memory fixed-window limiter keyed by client IP,
  configured via ``SARAL_RATE_LIMIT`` (requests/min, 0 disables).
"""

import os
import threading
import time

from fastapi import Header, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.app.core.logging_config import get_logger

logger = get_logger("security")


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency. No-op unless SARAL_API_KEY is configured."""
    expected = os.getenv("SARAL_API_KEY")
    if not expected:
        return  # auth disabled
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-IP rate limiter (in-memory)."""

    def __init__(self, app, limit: int | None = None, window: int = 60) -> None:
        super().__init__(app)
        self.limit = limit if limit is not None else int(os.getenv("SARAL_RATE_LIMIT", "60"))
        self.window = window
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        if self.limit <= 0:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window

        with self._lock:
            q = self._hits.setdefault(ip, [])
            while q and q[0] < window_start:
                q.pop(0)
            if len(q) >= self.limit:
                logger.warning(f"Rate limit exceeded ip={ip} limit={self.limit}/{self.window}s")
                return JSONResponse(
                    {"detail": "Rate limit exceeded. Please slow down."},
                    status_code=429,
                )
            q.append(now)

        return await call_next(request)
