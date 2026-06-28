"""
Cache layer for the S.A.R.A.L. backend.

Uses Redis when ``REDIS_URL`` is set; otherwise falls back to a process-local
in-memory TTL cache (so the app works with zero infra in dev). Values are
stored as JSON strings; build keys with :meth:`Cache.make_key`.
"""

import hashlib
import json
import os
import threading
import time
from typing import Optional

from backend.app.core.logging_config import get_logger

logger = get_logger("cache")


class _MemoryCache:
    def __init__(self) -> None:
        self._d: dict[str, tuple[str, Optional[float]]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            entry = self._d.get(key)
            if not entry:
                return None
            value, expires = entry
            if expires is not None and expires < time.time():
                self._d.pop(key, None)
                return None
            return value

    def set(self, key: str, value: str, ttl: int) -> None:
        with self._lock:
            self._d[key] = (value, time.time() + ttl if ttl else None)


class Cache:
    def __init__(self) -> None:
        self.kind = "memory"
        self._redis = None
        self._mem = _MemoryCache()

        url = os.getenv("REDIS_URL")
        if url:
            try:
                import redis

                self._redis = redis.Redis.from_url(url, decode_responses=True)
                self._redis.ping()
                self.kind = "redis"
                logger.info("Cache backend=redis")
            except Exception as e:  # pragma: no cover - infra dependent
                logger.warning(f"Redis unavailable ({e}); using in-memory cache")
                self._redis = None
        else:
            logger.info("Cache backend=memory (set REDIS_URL to use Redis)")

    def get(self, key: str) -> Optional[str]:
        if self._redis is not None:
            try:
                return self._redis.get(key)
            except Exception as e:  # pragma: no cover
                logger.warning(f"Redis get failed ({e}); falling back to memory")
        return self._mem.get(key)

    def set(self, key: str, value: str, ttl: int = 3600) -> None:
        if self._redis is not None:
            try:
                self._redis.set(key, value, ex=ttl)
                return
            except Exception as e:  # pragma: no cover
                logger.warning(f"Redis set failed ({e}); falling back to memory")
        self._mem.set(key, value, ttl)

    @staticmethod
    def make_key(prefix: str, payload: dict) -> str:
        digest = hashlib.sha1(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return f"{prefix}:{digest}"


# Module-level singleton
cache = Cache()
