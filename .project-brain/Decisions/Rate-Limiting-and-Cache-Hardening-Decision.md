---
type: decision
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[FastAPI-Backend]]"
  - "[[Eligibility-Engine]]"
---

# Decision: Redis Caching and IP-Based Rate Limiting

## Context & Problem
Running RAG retrieval and LLM evaluation processes is computationally expensive.
1. Repeated queries for identical demographic profiles (such as clicking the "Run Recommendation" button multiple times) result in redundant database requests and LLM costs.
2. Unprotected endpoints are vulnerable to denial-of-service (DoS) attempts and API key abuse.

---

## Options Considered
1. **No Caching or Rate-Limiting:** Handle all requests dynamically.
   * *Cons:* Security risk and high API operational costs.
2. **Hybrid Caching and In-Memory Rate-Limiting Middleware:** Implement a hybrid cache layer (uses Redis if available; falls back to an in-memory dictionary) and rate-limit client IPs.
   * *Pros:* Prevents duplicate processing and protects backend services.

---

## Choice Made
* **Hybrid Cache & Rate-Limiting:** Implemented in [cache.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/core/cache.py) and [security.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/core/security.py) (Phase 5).
* Caches recommendation results for 1 hour using a SHA-1 hash of the profile parameters as the key.
* The rate-limiting middleware blocks IPs that exceed 60 requests/minute, returning HTTP 429.

---

## Trade-offs & Consequences
* **Pros:** Cuts API costs and protects services from key abuse. Falls back to in-memory caching if Redis is not configured, simplifying local development.
* **Cons:** In-memory caching/rate-limiting states are lost on server restarts. Standardizing on Redis is required for production scaling across multiple server instances.
