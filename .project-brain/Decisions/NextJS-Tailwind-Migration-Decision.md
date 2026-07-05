---
type: decision
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[NextJS-Frontend]]"
  - "[[Streamlit-Interface]]"
---

# Decision: Migration to Next.js & Tailwind CSS Frontend

## Context & Problem
Originally, S.A.R.A.L. used a Streamlit python frontend dashboard ([app.py](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/frontend/app.py)) to collect demographics and display cards. While Streamlit allowed rapid prototyping, it suffered from:
1. Limited UI layout customization (e.g. rigid grid configurations, layout truncation bugs, and lack of support for custom animations).
2. Monolithic script re-runs that reload the entire page state on minor changes.
3. Lack of modular design patterns (such as standard Backend-for-Frontend controllers).

---

## Options Considered
1. **Optimize Streamlit:** Write custom CSS and JavaScript wrappers within Streamlit to handle animations and API routes.
   * *Cons:* Complex and goes against Streamlit's design patterns.
2. **Next.js & Tailwind CSS Rewrite:** Migrate primary UI components to a decoupled TypeScript frontend application under `/web`.
   * *Pros:* Extensible layout designs, custom gradients, Framer Motion animations, SSE streaming support, and internationalization handlers.

---

## Choice Made
* **Next.js Rewrite:** Migrated user interfaces to Next.js in Phase 3.
* The legacy Streamlit code is retained for cloud fallbacks (`DEPLOYMENT_ENV="CLOUD"`).

---

## Trade-offs & Consequences
* **Pros:** Responsive glassmorphic layout configurations, streaming chat, localized interfaces (`next-intl`), and web speech integrations.
* **Cons:** Increases project complexity, introducing a second runtime engine (Node.js/Next.js) alongside the FastAPI Python backend.
