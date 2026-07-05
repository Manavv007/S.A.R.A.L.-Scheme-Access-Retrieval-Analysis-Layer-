---
type: component
project: S.A.R.A.L.
status: completed
confidence: confirmed
created: 2026-07-05
related:
  - "[[FastAPI-Backend]]"
  - "[[System-Overview]]"
---

# Next.js Frontend Component

The primary user interface for S.A.R.A.L. is hosted under the [web/](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/web/) directory. It represents the modern rewrite of the interface, replacing the Streamlit front-end for production environments.

---

## 1. Key Technologies
* **Framework:** Next.js (App Router) + TypeScript.
* **Styling:** Tailwind CSS + `shadcn/ui` components.
* **Animations:** Framer Motion for smooth glassmorphic card loading, skeleton transitions, and profile wizards.
* **Visuals:** Custom particle-effect WebGL background over dark emerald/violet gradients (`#0a0a0a` base theme).
* **Multilingual support:** Integrated with `next-intl` to dynamically translate dashboard layouts and messages into 6 regional languages (English, Hindi, Gujarati, Tamil, Telugu, Marathi).

---

## 2. Technical Design Patterns

### A. Backend-for-Frontend (BFF) Proxying
To prevent the client from accessing FastAPI endpoints directly and to secure the optional `SARAL_API_KEY`, Next.js Route Handlers act as a proxy layer.
* **Chat Stream Router ([route.ts](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/web/src/app/api/chat/route.ts)):** Maps incoming chat queries to backend FastAPI stream endpoints, piping the HTTP chunk response payload straight back to client browsers for token-by-token rendering.
* **Recommend Router ([route.ts](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/web/src/app/api/recommend/route.ts)):** Forwards demographic profiles to the FastAPI `/recommend` endpoint, keeping target server configurations hidden.

### B. Multi-Step Profile Wizard ([profile-wizard.tsx](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/web/src/components/profile-wizard.tsx))
User data is captured through a multi-step form progress wizard. This reduces form fatigue and validates inputs (like parsing numeric values for age and income limits) before shipping payloads.

### C. Voice Integration
* **Speech-to-Text:** Implemented local voice capture via web-speech APIs, allowing users to ask chat queries in native languages orally.
* **Text-to-Speech ([use-speech.ts](file:///c:/Users/BAPS/OneDrive%20-%20pdpu.ac.in/Documents/AI_LAB_NEW/web/src/lib/use-speech.ts)):** Dynamic read-aloud component that narrates scheme benefits and reasons in regional languages.

---

## 3. Communication Flows

```
[ Citizen Browser ]
       │ 
       ├── (User Input: Age, Income, Occupation) ──▶ [ Profile Wizard ]
       ├── (Oral Query) ──▶ [ use-speech.ts ]
       │ 
       ▼
[ BFF Route Handlers ] (Proxy API calls, appends headers)
       │
       ▼ (HTTP POST)
[ FastAPI Server ] (`/chat/stream` or `/recommend`)
```
