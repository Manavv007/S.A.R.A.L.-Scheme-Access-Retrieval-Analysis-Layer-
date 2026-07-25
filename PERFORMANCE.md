# Performance & Load Test Results

Load tests were run locally against the FastAPI backend (`http://localhost:8000`) using [Locust](https://locust.io/), with API-key auth and **Redis (Upstash)** enabled for recommendation caching.

| Tool | Locust 2.46 |
|---|---|
| Target | `POST /api/v1/recommend`, `POST /api/v1/chat` |
| Hardware | Local Windows development machine |
| Date | July 2026 |

> LLM-backed routes (Groq + Pinecone RAG) are latency-bound by design. These numbers measure **end-to-end API reliability and scaling behaviour**, not raw microservice RPS.

---

## Headline results

| Concurrent users | Duration | Total requests | Failures | Approx. RPS |
|---|---|---|---|---|
| **5** | 1 min | 112 | **0%** | ~1.9 |
| **20** | 3 min | 296 | **0%** | ~1.7 |
| **50** | 2 min | 222 | **0%** | ~2.2 |

**Takeaway:** Under all three loads the API stayed **error-free (0% failures)**. Throughput stays ~2 req/s because each request may call an external LLM — more users increase **queue wait**, not raw RPS.

---

## Latency by scenario

### Light load — 5 users (spawn 1/s, 1 min)

Best-case UX; Redis cache hits dominate `/recommend`.

| Endpoint | # reqs | Median | Avg | p95 | Max | Failures |
|---|---|---|---|---|---|---|
| `POST /api/v1/recommend` | 92 | **53 ms** | 435 ms | ~2.1 s | 3.7 s | 0% |
| `POST /api/v1/chat` | 20 | **1.1 s** | 1.2 s | ~2.0 s | 2.0 s | 0% |
| **Aggregated** | **112** | **150 ms** | 573 ms | ~2.0 s | 3.7 s | **0%** |

Cached `/recommend` responses regularly land in the **30–80 ms** range (min observed: **30 ms**).

### Medium load — 20 users (spawn 2/s, 3 min)

Stable, but interactive latency degrades as LLM calls queue.

| Endpoint | # reqs | Median | Avg | p95 | Max | Failures |
|---|---|---|---|---|---|---|
| `POST /api/v1/recommend` | 220 | 7.5 s | 9.2 s | ~23 s | 27 s | 0% |
| `POST /api/v1/chat` | 76 | 10 s | 12 s | ~27 s | 28 s | 0% |
| **Aggregated** | **296** | 7.9 s | 9.9 s | ~25 s | 28 s | **0%** |

### Stress load — 50 users (spawn 5/s, 2 min)

Still **zero failures**; most time is spent waiting on the LLM/RAG pipeline under contention.

| Endpoint | # reqs | Median | Avg | p95 | Max | Failures |
|---|---|---|---|---|---|---|
| `POST /api/v1/recommend` | 172 | 12 s | 18 s | ~47 s | 48 s | 0% |
| `POST /api/v1/chat` | 50 | 17 s | 21 s | ~48 s | 48 s | 0% |
| **Aggregated** | **222** | 12 s | 19 s | ~47 s | 48 s | **0%** |

---

## What this shows

| Strength | Evidence |
|---|---|
| **Reliability** | 0% failure rate across 5 → 50 concurrent users |
| **Redis caching** | Cached `/recommend` ≈ **30–53 ms** under light load |
| **Auth hardening** | All requests used `X-API-Key`; no auth-related errors |
| **Graceful degradation** | Latency rises under load; the service does not crash or return 5xx storms |

| Constraint | Why |
|---|---|
| Low RPS (~2) | Each request may invoke Groq + Pinecone |
| High p95 at 20–50 users | Concurrent LLM work queues on a single backend process |
| Cold / uncached recommend | Full RAG + eligibility path is multi-second by nature |

---

## Capacity guidance

| Concurrent users | Expected experience |
|---|---|
| **≤ 5** | Snappy for cached recommend; chat ~1–2 s |
| **~20** | Fully reliable; responses often multi-second |
| **~50** | Fully reliable under stress; expect long waits (tens of seconds) |

Suitable for **demos, pilots, and soft launches**. Horizontal scaling, request coalescing (single-flight cache), and/or async job queues would be the next steps for higher interactive concurrency.

---

## How to reproduce

```powershell
# Optional: disable rate limit for the test window
# SARAL_RATE_LIMIT=0 in .env, then restart the backend

$env:SARAL_API_KEY = "<same value as backend .env>"

pip install locust
locust -f locustfile.py --host http://localhost:8000 --users 5 --spawn-rate 1 --run-time 1m --headless
locust -f locustfile.py --host http://localhost:8000 --users 20 --spawn-rate 2 --run-time 3m --headless
locust -f locustfile.py --host http://localhost:8000 --users 50 --spawn-rate 5 --run-time 2m --headless
```

Restore `SARAL_RATE_LIMIT` after testing.
