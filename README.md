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

```
┌─────────────────────┐         ┌─────────────────────────────────┐
│   Streamlit Frontend │ ◄─────► │       FastAPI Backend            │
│   (frontend/app.py) │  HTTP   │   ┌───────────────────────────┐ │
│                     │         │   │  Recommendation Service   │ │
│  • Profile Form     │         │   │  (Multi-Vector Retrieval) │ │
│  • Scheme Cards     │         │   │         │                 │ │
│  • Chat Interface   │         │   │    ┌────▼────┐  ┌───────┐ │ │
│  • Multilingual UI  │         │   │    │ Pinecone│  │ Groq  │ │ │
│                     │         │   │    │ (RAG)   │  │ (LLM) │ │ │
│                     │         │   │    └─────────┘  └───────┘ │ │
└─────────────────────┘         │   └───────────────────────────┘ │
                                └─────────────────────────────────┘
```

---

## Project Structure

```
S.A.R.A.L/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI route handlers (chat, schemes)
│   │   ├── core/config.py   # Pydantic settings (.env loader)
│   │   ├── models/dtos.py   # Data transfer objects
│   │   ├── services/
│   │   │   ├── llm_engine.py        # Groq LLM wrapper (with chat memory)
│   │   │   ├── rag_retriever.py     # Pinecone RAG + query expansion
│   │   │   └── recommendation.py    # Multi-vector retrieval + Researcher-Critic loop + grounded verdicts
│   │   └── main.py          # Uvicorn entrypoint
│   ├── scripts/             # Ingestion & test scripts
│   └── requirements.txt
├── frontend/
│   ├── app.py               # Streamlit UI (premium dark theme)
│   └── src/utils/api_client.py
├── data/raw_pdfs/           # Government scheme PDFs
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

### 4. Start the Backend

```bash
python -m backend.app.main
```

The API will be available at `http://localhost:8000`.

### 5. Start the Frontend

```bash
streamlit run frontend/app.py
```

The UI will open at `http://localhost:8501`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit (custom CSS, dark theme) |
| **Backend** | FastAPI + Uvicorn |
| **LLM** | Groq (LLaMA) via LangChain |
| **Vector DB** | Pinecone |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` |
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
