---
title: S.A.R.A.L.
emoji:
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.39.0
app_file: frontend/app.py
pinned: false
---
<p align="center">
  <h1 align="center">S.A.R.A.L.-Scheme-Access-Retrieval-Analysis-Layer</h1>
  <p align="center"><b>Scheme Access, Retrieval, Analysis & Layer</b></p>
  <p align="center">AI-powered assistant that helps Indian citizens discover government schemes they're eligible for.</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-15-000000?logo=nextdotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/LangChain--green" />
  <img src="https://img.shields.io/badge/Groq-LLM-orange" />
  <img src="https://img.shields.io/badge/Pinecone-Vector_DB-blue" />
</p>

---

## Features

| Feature | Description |
|---|---|
| **Smart Scheme Matching** | RAG-based retrieval from government PDFs + LLM-powered eligibility analysis |
| **Self-Correcting Retrieval** | Multi-vector retrieval + a Researcher-Critic loop: a Critic LLM judges context relevance and retries with a refined query (up to 3×), then candidate re-ranking before LLM analysis |
| **Multilingual Support** | UI & responses in **English, Hindi, Gujarati, Telugu, Marathi, Tamil** |
| **AI Chat Advisor** | Conversational chatbot with memory — ask follow-up questions naturally |
| **Document Query Expansion** | Auto-expands "What documents do I need?" queries for better RAG retrieval |

---

## Architecture

Decoupled and **HTTP-only** — FastAPI is the single integration surface. The **Next.js** app is the primary UI (calling FastAPI through server-side BFF Route Handlers); the **Streamlit** app is the secondary UI and Hugging Face Spaces deployment target.

```
┌──────────────────────┐
│  Next.js (web/)      │  primary UI ─┐ fetch
│  :3000               │              │
│  • Profile wizard    │        ┌─────▼──────────┐        ┌─────────────────────────────────┐
│  • Scheme cards      │        │ BFF Route      │  HTTP  │       FastAPI Backend  :8000     │
│  • Streaming chat    │───────►│ Handlers       │───────►│   ┌───────────────────────────┐ │
│  • i18n + voice      │        │ (app/api/*)    │        │   │  Recommendation Service   │ │
└──────────────────────┘        └────────────────┘        │   │  (Multi-Vector + Critic)  │ │
                                                           │   │         │                 │ │
┌──────────────────────┐                                  │   │    ┌────▼────┐  ┌───────┐ │ │
│  Streamlit           │  secondary UI / HF Spaces        │   │    │ Pinecone│  │ Groq  │ │ │
│  (frontend/app.py)   │──────────── HTTP ───────────────►│   │    │ (RAG)   │  │ (LLM) │ │ │
│  :8501               │                                  │   │    └─────────┘  └───────┘ │ │
└──────────────────────┘                                  │   └───────────────────────────┘ │
                                                           └─────────────────────────────────┘
```

---

## Project Structure

```
S.A.R.A.L/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routes: chat.py, schemes.py, admin.py
│   │   ├── core/            # config, security (rate limit), cache, logging
│   │   ├── models/dtos.py   # Data transfer objects
│   │   ├── services/
│   │   │   ├── llm_engine.py        # Groq LLM wrapper (with chat memory)
│   │   │   ├── rag_retriever.py     # Pinecone RAG + query expansion
│   │   │   └── recommendation.py    # Multi-vector retrieval + Researcher-Critic loop + grounded verdicts
│   │   └── main.py          # FastAPI/Uvicorn entrypoint (HTTP-only)
│   ├── scripts/             # Ingestion & DB utilities
│   └── requirements.txt
├── web/                     # PRIMARY frontend — Next.js 15 + TS + Tailwind
│   ├── src/app/             # pages + BFF Route Handlers (api/chat, api/recommend)
│   ├── src/components/      # scheme cards, chat panel, profile wizard, ...
│   ├── messages/            # 6-language i18n catalogs (next-intl)
│   └── tests/               # Playwright e2e smoke tests
├── frontend/                # SECONDARY frontend — Streamlit (HF Spaces target)
│   ├── app.py               # Streamlit UI (premium dark theme)
│   └── src/utils/api_client.py   # HTTP client to FastAPI
├── scraper/                 # Scrapy-Playwright ingestion service
├── tests/                   # Backend pytest suites
├── data/raw_pdfs/           # Government scheme PDFs
├── .github/workflows/       # CI: scrape.yml, sync_to_hf.yml
├── start.bat                # One-command launcher (backend + Next.js)
├── .env                     # API keys (git-ignored)
└── .gitignore
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Manavv007/S.A.R.A.L.-Scheme-Access-Retrieval-Analysis-Layer-.git
cd S.A.R.A.L.-Scheme-Access-Retrieval-Analysis-Layer-
pip install -r backend/requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENV=your_pinecone_environment
PINECONE_INDEX_NAME=your_index_name
```

### 3. Ingest PDFs into Pinecone

```bash
python -m backend.scripts.ingest_pdfs
```

### 4. Run everything — one command (Windows)

```bash
start.bat
```

This launches the **FastAPI backend** (`http://localhost:8000`) and the **Next.js frontend** (`http://localhost:3000`) in two windows. On first run it auto-installs the frontend dependencies (`npm install` in `web/`).

<details>
<summary>Prefer to start each service manually?</summary>

```bash
# Backend  -> http://localhost:8000
python -m backend.app.main

# Primary frontend (Next.js) -> http://localhost:3000
cd web
npm install        # first time only
npm run dev

# Secondary frontend (Streamlit) -> http://localhost:8501
streamlit run frontend/app.py
```

The Next.js app reads the backend URL from `web/.env.local` (`BACKEND_URL`, default `http://localhost:8000/api/v1`). The Streamlit app uses `SARAL_API_BASE_URL` / `BACKEND_URL`.
</details>

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Primary Frontend** | Next.js 15 (App Router) + TypeScript + Tailwind CSS + Framer Motion, `next-intl` i18n, browser voice I/O |
| **Secondary Frontend** | Streamlit (custom CSS, dark theme) — Hugging Face Spaces deploy target |
| **Backend** | FastAPI + Uvicorn (rate limiting, Redis/in-memory cache) |
| **LLM** | Groq (LLaMA `llama-3.3-70b-versatile`) via LangChain |
| **Vector DB** | Pinecone |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` |
| **Ingestion** | Scrapy-Playwright crawler (idempotent, incremental) |
| **Data** | Government scheme PDFs |

---

## How the Retrieval Pipeline Works

1. **Researcher (Multi-Vector)** — Runs three retrieval strategies (semantic, keyword, national) against Pinecone with a **server-side metadata filter** (Central + user's state), then merges + de-duplicates the results
2. **Critic (Researcher-Critic loop)** — A Critic LLM judges whether the retrieved context is relevant to the user's occupation/state; on FAIL it proposes a refined query and the Researcher retries (up to 3×)
3. **Re-ranking** — Candidate docs are re-ranked by MiniLM similarity to the profile, keeping the most relevant for the limited LLM context window
4. **Verdict Generator** — Produces structured JSON (scheme name, status, reason) **grounded** with each scheme's `source_url` / `apply_url`

---

## Supported Languages

| Language | UI | Chat | Scheme Reasons |
|---|---|---|---|
| English | | | |
| Hindi | | | |
| Gujarati | | | |
| Telugu | | | |
| Marathi | | | |
| Tamil | | | |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/recommend` | Get eligible schemes for a user profile |
| `POST` | `/api/v1/chat` | Chat with the AI advisor |
| `POST` | `/api/v1/chat/stream` | Streaming (SSE) chat responses, token-by-token |
| `GET`  | `/api/v1/admin/crawl-stats` | Crawler ingestion stats (JSON; `/view` for HTML) |
