---
type: decision
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[NextJS-Frontend]]"
  - "[[FastAPI-Backend]]"
---

# Decision: BFF Proxy & Server-Sent Events (SSE) Streaming Chat

## Context & Problem
FastAPI endpoints use custom JSON authorization headers (`X-API-Key`) to validate requests. Accessing these backend endpoints directly from the user's browser:
1. Exposes authorization keys in network traces.
2. Breaks CORS settings if FastAPI runs on a separate subdomain.
3. Chat responses returned as single large payloads result in high perceived latency.

---

## Options Considered
1. **Direct Browser to FastAPI Connection:** Call FastAPI routes directly.
   * *Cons:* Security risk and poor user experience (long wait for full response text).
2. **Next.js BFF (Backend-for-Frontend) Proxy with SSE:** Proxy calls via Next.js Route Handlers and stream FastAPI's response token-by-token.
   * *Pros:* Hides API keys on the server side and streams chat output.

---

## Choice Made
* **Next.js BFF Proxy with SSE:** Implemented in [route.ts](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/web/src/app/api/chat/route.ts). FastAPI streams text tokens using `StreamingResponse` ([chat.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/backend/app/api/v1/chat.py)), and the Next.js Route Handler pipes the stream directly to the client browser.

---

## Trade-offs & Consequences
* **Pros:** Enhances security by keeping the FastAPI URL and API keys server-side. Improves UX by rendering assistant responses progressively.
* **Cons:** Increases server load, as streaming connections must remain open for the duration of the request.
