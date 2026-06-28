"""Tests for Phase 5 hardening: cache, auth, rate limiting, admin endpoint."""

import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.core.cache import Cache
from backend.app.core.security import RateLimitMiddleware


# ── Cache ──
def test_cache_memory_get_set():
    c = Cache()
    c.set("k1", "v1", ttl=60)
    assert c.get("k1") == "v1"
    assert c.get("missing") is None


def test_cache_ttl_expiry():
    c = Cache()
    c.set("k2", "v2", ttl=1)
    assert c.get("k2") == "v2"
    time.sleep(1.1)
    assert c.get("k2") is None


def test_cache_make_key_deterministic():
    p = {"occupation": "Farmer", "state": "Gujarat", "income": "1"}
    assert Cache.make_key("recommend", p) == Cache.make_key("recommend", dict(reversed(list(p.items()))))
    assert Cache.make_key("recommend", p) != Cache.make_key("recommend", {"occupation": "Student"})


# ── Rate limiting (isolated app) ──
def test_rate_limit_blocks_after_limit():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limit=2, window=60)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 429  # third exceeds limit


# ── API-key auth ──
def test_api_key_enforced(monkeypatch):
    monkeypatch.setenv("SARAL_API_KEY", "secret123")

    from backend.app.api.v1.admin import router as admin_router

    app = FastAPI()
    app.include_router(admin_router, prefix="/api/v1")
    client = TestClient(app)

    # No key -> 401
    assert client.get("/api/v1/admin/crawl-stats").status_code == 401
    # Correct key -> 200
    r = client.get("/api/v1/admin/crawl-stats", headers={"X-API-Key": "secret123"})
    assert r.status_code == 200
    assert "tracked_schemes" in r.json()


def test_api_key_disabled_when_unset(monkeypatch):
    monkeypatch.delenv("SARAL_API_KEY", raising=False)

    from backend.app.api.v1.admin import router as admin_router

    app = FastAPI()
    app.include_router(admin_router, prefix="/api/v1")
    client = TestClient(app)

    # Auth disabled -> open
    assert client.get("/api/v1/admin/crawl-stats").status_code == 200
