# S.A.R.A.L. Web (Next.js Frontend)

Premium frontend for S.A.R.A.L. — Next.js App Router + TypeScript + Tailwind CSS
+ Framer Motion, with a canvas constellation background over a near-black theme,
glassmorphic components, a multi-step profile wizard, and a token-streaming AI
chat advisor.

## Stack

- Next.js 15 (App Router, React 19)
- TypeScript + Tailwind CSS
- Framer Motion (micro-interactions)
- next-intl (6 languages: English, Hindi, Gujarati, Telugu, Marathi, Tamil)
- lucide-react icons

## Architecture (Backend-for-Frontend)

```
Browser ──► Next.js Route Handlers (BFF)        ──► FastAPI backend
            /api/recommend  (proxy JSON)             /api/v1/recommend
            /api/chat       (proxy token stream)     /api/v1/chat/stream
```

Route handlers run server-side and hold `BACKEND_URL`, so the FastAPI base URL
and any future API keys are never exposed to the browser. The chat handler pipes
the upstream token stream straight to the client for token-by-token rendering.

## Setup

```bash
cd web
npm install
cp .env.local.example .env.local   # set BACKEND_URL
npm run dev                         # http://localhost:3000
```

The FastAPI backend must be running (default `http://localhost:8000`):

```bash
# from repo root
python -m backend.app.main
```

## Scripts

| Command           | Purpose                       |
|-------------------|-------------------------------|
| `npm run dev`     | Dev server                    |
| `npm run build`   | Production build              |
| `npm run start`   | Serve the production build    |
| `npm run typecheck` | TypeScript check (no emit)  |

## Internationalization

`next-intl` with a cookie-based locale (no path prefixes). Translations live in
`messages/<locale>.json`. The language switcher writes the `SARAL_LOCALE` cookie
via a server action and refreshes; the backend response language is derived from
the chosen locale (`localeToBackendLanguage`).

## Hosting

- **Frontend → Vercel.** Import the repo, set the project root to `web/`, and add
  the `BACKEND_URL` environment variable pointing at the deployed backend.
- **Backend → a container host** (Render / Railway / Fly / HF Spaces Docker).
  Run `uvicorn backend.app.main:app`. Set `SARAL_CORS_ORIGINS` to the Vercel
  domain so the browser-side (non-BFF) calls are allowed; the BFF proxy itself is
  server-to-server and not subject to CORS.
```
Vercel (web/)  ──HTTPS──►  Backend host (FastAPI)  ──►  Pinecone + Groq
```
