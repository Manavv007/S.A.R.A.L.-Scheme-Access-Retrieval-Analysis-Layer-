# S.A.R.A.L. Project Architecture

This document describes the high-level system architecture, data workflows, and folder structure of **S.A.R.A.L. (Scheme Access, Retrieval, Analysis & Layer)**.

---

## System Architecture Overview

S.A.R.A.L. is built as a modular AI-powered Indian Government Scheme recommendation and consultation platform. It uses a **Retrieval-Augmented Generation (RAG)** pipeline combined with strict business logic filtering and a multi-vector query approach.

The system is **decoupled and HTTP-only**: a **FastAPI** backend is the single integration surface, and every frontend talks to it over HTTP REST.
- **Primary frontend — Next.js**: a TypeScript + Tailwind App Router app (`web/`) that calls FastAPI through server-side **BFF Route Handlers** (hides the API base URL/keys and enables token streaming).
- **Secondary frontend — Streamlit**: the legacy `frontend/app.py` UI, retained as the Hugging Face Spaces / Streamlit Cloud deployment target. It calls FastAPI directly over HTTP via `SARAL_API_BASE_URL` / `BACKEND_URL`.

> Note: an earlier design had a dual `DEPLOYMENT_ENV` mode where Streamlit imported backend services in-process. That was removed during the Next.js migration — there is no in-process/monolithic import path anymore.

```mermaid
graph TD
    %% Styling
    classDef client fill:#1e293b,stroke:#334155,stroke-width:2px,color:#f8fafc;
    classDef server fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef database fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#f8fafc;
    classDef external fill:#2d0b00,stroke:#f97316,stroke-width:2px,color:#f8fafc;

    subgraph ClientLayer ["Frontend Layer"]
        NextUI["Next.js App (web/, :3000)"]
        BFF["BFF Route Handlers (app/api/*)"]
        Streamlit["Streamlit App (frontend/app.py, :8501)"]
        NextUI <-->|fetch| BFF
    end

    subgraph ServiceLayer ["Backend Layer (FastAPI App, :8000)"]
        Routes["APIRouter (chat.py, schemes.py, admin.py)"]
        RecService["Recommendation Service"]
        RAGService["RAG Service"]
        LLMEngine["LLM Engine Wrapper"]

        Routes <--> RecService
        Routes <--> RAGService
        RecService <--> RAGService
        RecService <--> LLMEngine
        RAGService <--> LLMEngine
    end

    subgraph StorageLayer ["Knowledge & Vector Storage"]
        PDFs["Raw PDFs & Docs (data/raw_pdfs/)"]
        Pinecone[("Pinecone Vector DB")]
        Ingest["Ingestion (ingest_pdfs.py / scraper)"]

        PDFs -->|Read & Parse| Ingest
        Ingest -->|Embed via all-MiniLM-L6-v2| Pinecone
    end

    subgraph ExternalServices ["External LLM Provider"]
        Groq["Groq API (Llama-3.3-70b-versatile)"]
    end

    %% Communication paths (HTTP only)
    BFF <-->|HTTP POST /chat, /chat/stream, /recommend| Routes
    Streamlit <-->|HTTP POST /chat, /recommend| Routes

    RAGService <-->|Similarity Search| Pinecone
    LLMEngine <-->|Generate Answer / JSON| Groq

    class NextUI,BFF,Streamlit client;
    class Routes,RecService,RAGService,LLMEngine,Ingest server;
    class Pinecone,PDFs database;
    class Groq external;
```

---

## Detailed Workflows

### 1. Recommendation Retrieval & Analysis Pipeline

When a user submits their profile, the system executes a production-grade multi-vector retrieval process combined with strict metadata filtering and rules-based LLM analysis:

```mermaid
flowchart TD
    %% Styling
    classDef process fill:#1e293b,stroke:#334155,color:#f8fafc;
    classDef decision fill:#1e1b4b,stroke:#818cf8,color:#f8fafc;
    classDef start_end fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;

    Start([User Requests Recommendation]) --> Inputs[Extract Profile: Age, State, Occupation, Income, Caste, Language]

    subgraph RetrievalStage ["1. Multi-Vector Retrieval Pipeline"]
        Inputs --> GenQueries[Generate 3 Parallel Queries:<br>A. Semantic Search<br>B. Keyword/State Search<br>C. Broad National Search]
        GenQueries --> PineconeSearch[Query Pinecone Index (k=10 to 15)]
        PineconeSearch --> MergeDedup[Merge & Deduplicate Chunks by first 200 chars]
    end

    subgraph FilterStage ["2. Strict Metadata Filter"]
        MergeDedup --> FilterDocs{Does State Match?<br>Doc State == User State OR<br>Doc State is Central/Union OR<br>Doc State is Empty}
        FilterDocs -->|No| Reject[Discard Document Chunk]
        FilterDocs -->|Yes| Keep[Keep Document Chunk]
    end

    subgraph AnalysisStage ["3. Eligibility Verdict Engine"]
        Keep --> PromptBuild[Construct Prompt:<br>Apply Strict Occupation Logic<br>Apply Strict Income Limits<br>Apply Caste Constraints]
        PromptBuild --> LLMCall[Call LLM: Groq Llama-3.3-70b]
        LLMCall --> JSONParse[Extract and Parse JSON Array]
        JSONParse --> SchemeDedup[Deduplicate Schemes by Base Name prefix]
        SchemeDedup --> LanguageTrans[Translate 'reason' field to Selected Language]
    end

    LanguageTrans --> End([Return Final Recommendation List])

    class Start,End start_end;
    class Inputs,GenQueries,PineconeSearch,MergeDedup,Keep,Reject,PromptBuild,LLMCall,JSONParse,SchemeDedup,LanguageTrans process;
    class FilterDocs decision;
```

- **Parallel Vector Retrieval**: Resolves issues with embeddings missing broad national queries by checking:
  1. *Semantic Query*: Evaluates descriptive details.
  2. *Keyword/State Query*: Targeted lookup matching the state name.
  3. *National Fallback*: Direct query for Central/National schemes (e.g. Pradhan Mantri schemes).
- **Metadata State Filtering**: Guarantees that users are not shown state-specific schemes from regions they do not reside in.
- **Strict Logic Guards**: Prompt rules strictly limit matching based on occupation (e.g. Students, Farmers, Business), caste categories, and income limits.

---

### 2. Document Ingestion Pipeline

The ingestion pipeline handles loading documents, extracting metadata, and splitting them for embedding extraction:

```mermaid
flowchart LR
    classDef step fill:#1e293b,stroke:#334155,color:#f8fafc;
    classDef start_end fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;

    Start([Scan data/raw_pdfs/]) --> Walk[Recursively find PDF, CSV, JSON, TXT]
    Walk --> ForEach[For Each File]
    ForEach --> Loader[Load document contents based on Extension]
    Loader --> Meta[Smart Metadata Tagging:<br>Set 'state' = parent folder name<br>Set 'source_file' = file name]
    Meta --> Chunk[Split text using RecursiveCharacterTextSplitter<br>chunk_size=1000, overlap=200]
    Chunk --> Embed[Embed chunks with all-MiniLM-L6-v2]
    Embed --> Upsert[Upsert to Pinecone Vector Index]
    Upsert --> Next{More Files?}
    Next -->|Yes| ForEach
    Next -->|No| End([Ingestion Complete])

    class Start,End start_end;
    class Walk,ForEach,Loader,Meta,Chunk,Embed,Upsert step;
```

---

## Directory Structure

```
S.A.R.A.L/
├── backend/                      # The Intelligence Layer (Python/FastAPI)
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── chat.py           # /chat and /chat/stream (SSE token streaming)
│   │   │   │   ├── schemes.py        # /recommend (eligibility matching)
│   │   │   │   └── admin.py          # /admin/crawl-stats (+ HTML view)
│   │   ├── core/
│   │   │   ├── config.py             # Env variables & Pydantic Config settings
│   │   │   ├── security.py           # Rate-limit middleware
│   │   │   ├── cache.py              # Redis / in-memory recommendation cache
│   │   │   └── logging_config.py     # Structured logging setup
│   │   ├── models/
│   │   │   └── dtos.py               # Request/Response Data Transfer Objects (Pydantic)
│   │   ├── services/                 # core business logic
│   │   │   ├── llm_engine.py         # Groq LLM wrapper with custom prompts & history
│   │   │   ├── rag_retriever.py      # Pinecone query logic & query expansion (Documents)
│   │   │   └── recommendation.py     # Multi-vector search, Researcher-Critic loop, re-ranking, verdicts
│   │   └── main.py                   # FastAPI entrypoint (HTTP-only, CORS, rate limiting)
│   ├── scripts/                      # DB utilities and ingestion
│   │   ├── ingest_pdfs.py            # PDF metadata loader and parser (idempotent upserts)
│   │   └── reset_db.py               # Wipes Pinecone indexes
│   └── requirements.txt              # Backend libraries
│
├── web/                          # PRIMARY frontend (Next.js 15 + TS + Tailwind)
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # Main page (profile wizard, cards, chat)
│   │   │   ├── layout.tsx            # Root layout + i18n provider
│   │   │   └── api/                  # BFF Route Handlers (server-side proxy to FastAPI)
│   │   │       ├── chat/route.ts     # Proxies + streams /chat
│   │   │       └── recommend/route.ts# Proxies /recommend
│   │   ├── components/               # UI (scheme-card, chat-panel, profile-wizard, ...)
│   │   ├── lib/                      # types, server-config, speech hooks
│   │   └── i18n/                     # next-intl config
│   ├── messages/                     # en, hi, gu, te, mr, ta translation catalogs
│   ├── tests/                        # Playwright e2e smoke tests
│   └── package.json
│
├── frontend/                     # SECONDARY frontend (Streamlit; HF Spaces target)
│   ├── src/utils/api_client.py       # HTTP client to FastAPI (SARAL_API_BASE_URL / BACKEND_URL)
│   └── app.py                        # Main UI and State Manager
│
├── scraper/                      # Scrapy-Playwright ingestion service
│   ├── saral_scraper/                # spiders, pipelines, normalize, statestore
│   ├── run.py                        # CrawlerProcess entrypoint
│   └── scrapy.cfg
│
├── tests/                        # Backend pytest suites (recommendation, normalize, hardening, ...)
│
├── n8n-workflows/                # The Automation Layer (WhatsApp/email/db-sync hooks)
│
├── data/                         # Core Knowledge Base
│   ├── raw_pdfs/                     # User-added PDFs and scheme guidelines
│   ├── processed/                    # Extracted scheme JSON + crawl_state.sqlite
│   └── templates/                    # Dynamic templates for auto-filled application forms
│
├── .github/workflows/            # CI: scrape.yml (scheduled crawl), sync_to_hf.yml (deploy)
├── docs/                         # Extended API and Setup guidelines
├── start.bat                     # One-command launcher (backend :8000 + Next.js :3000)
├── docker-compose.yml            # Docker Orchestration config
├── ARCHITECTURE.md               # This document
└── README.md                     # General project manual
```

---

## Technology Stack Breakdown

* **Primary Frontend**: Next.js 15 (App Router) + TypeScript + Tailwind CSS, with Framer Motion micro-interactions, a WebGL particle background, `next-intl` i18n (6 languages), and browser speech-to-text / read-aloud. Talks to the backend through server-side BFF Route Handlers.
* **Secondary Frontend**: Streamlit (`frontend/app.py`) with a custom dark theme — retained as the Hugging Face Spaces / Streamlit Cloud deployment target; calls FastAPI over HTTP.
* **API Framework**: FastAPI, chosen for async support, automatic OpenAPI/Swagger documentation, and performance. Adds per-IP rate limiting and a Redis (or in-memory) recommendation cache.
* **Vector Store**: Pinecone (Serverless index).
* **Embeddings**: `all-MiniLM-L6-v2` via HuggingFace (locally calculated to minimize latency).
* **Large Language Model (LLM)**: Groq Cloud API executing `llama-3.3-70b-versatile`.
* **Ingestion**: Scrapy-Playwright crawler (`scraper/`) with idempotent, incremental upserts; scheduled via GitHub Actions.
* **Automations**: `n8n` workflows configured for user alerts via WhatsApp and email syncs.

---

## End-to-End Query-Response Workflow

Below is a detailed visual representation of the lifecycle of a query—from the moment a user submits an input or runs an eligibility check in the web UI (Next.js primary, Streamlit secondary), to the final rendering of processed, translated results. The frontend differs but the backend flow is identical.

```text
+-------------------------------------------------------------------------------------------------+
|                                     USER QUERY WORKFLOW                                         |
+-------------------------------------------------------------------------------------------------+
|                                                                                                 |
|   [ USER INPUT ]                                                                                |
|         │                                                                                       |
|         ▼                                                                                       |
|   +───────────────────────────────+                                                             |
|   │      Streamlit Frontend       │ (Inputs: Age, State, Occupation, Income, Caste, Query)       |
|   +───────────────┬───────────────+                                                             |
|                   │                                                                             |
|                   │ (Next.js: fetch -> BFF proxy; Streamlit: direct HTTP)                       |
|                   ▼                                                                             |
|   +───────────────────────────────+                                                             |
|   │     FastAPI Router / Client   │ (Routes /recommend or /chat request)                        |
|   +───────────────┬───────────────+                                                             |
|                   │                                                                             |
|                   ├──────────────────────────────────┐                                          |
|                   ▼ (A. Retrieve Context)            ▼ (B. Process Recommendation)              |
|   +───────────────────────────────+            +───────────────────────────────+                |
|   │          RAG Service          │            │    Recommendation Service     │                |
|   +───────────────┬───────────────+            +───────────────┬───────────────+                |
|                   │                                            │                                |
|                   │ 1. [Query Expansion]                       │ 1. [Multi-Vector Search]       |
|                   │    (Appends doc keywords)                  │    (Semantic + Keyword + Nat.) |
|                   │ 2. [Pinecone Query]                        │ 2. [Metadata State Filter]     |
|                   │                                            │    (Keeps User State/Central)  |
|                   ▼                                            │                                |
|         +───────────────────+                                  ▼                                |
|         │   Pinecone DB     │ <────────────────────────────────┘                                |
|         +─────────┬─────────+   (Fetches top-K document chunks)                                 |
|                   │                                                                             |
|                   │ (Retrieved Excerpts)                                                        |
|                   ▼                                                                             |
|   +───────────────────────────────+                                                             |
|   │       LLM Engine Wrapper      │ (Builds template with Context + Eligibility constraints)     |
|   +───────────────┬───────────────+                                                             |
|                   │                                                                             |
|                   │ (Custom System Prompt)                                                      |
|                   ▼                                                                             |
|         +───────────────────+                                                                   |
|         │  Groq Cloud API   │ (Llama-3.3-70b-versatile Model Execution)                             |
|         +─────────┬─────────+                                                                   |
|                   │                                                                             |
|                   │ (Raw Answer / JSON Verdict Array)                                           |
|                   ▼                                                                             |
|   +───────────────────────────────+                                                             |
|   │     Post-Processing Layer     │ 1. Extracts & Parses JSON Array                             |
|   │    (Recommendation.py)         │ 2. Deduplicates by Base Scheme Name                         |
|   │                               │ 3. Translates Verdict Reason to Selected Language           |
|   +───────────────┬───────────────+                                                             |
|                   │                                                                             |
|                   │ (Cleaned & Translated Result Payload)                                       |
|                   ▼                                                                             |
|   +───────────────────────────────+                                                             |
|   │       Streamlit Dashboard     │ (Renders Glassmorphic cards or streams Chat responses)      |
|   +───────────────┬───────────────+                                                             |
|                   │                                                                             |
|                   ▼                                                                             |
|   [ USER VIEW / RESULT ]                                                                        |
|                                                                                                 |
+-------------------------------------------------------------------------------------------------+
```

### Workflow Steps Breakdown:

1. **User Input Collection**: The user enters their demographic details (age, state, occupation, income, caste) and chooses a language. They either submit a chat query or request a scheme recommendation check.
2. **API Dispatching**: The frontend sends the request to FastAPI over HTTP:
   * *Next.js*: the browser calls a same-origin BFF Route Handler (`web/src/app/api/*`), which server-side proxies (and streams) to FastAPI's `/api/v1/chat`, `/api/v1/chat/stream`, or `/api/v1/recommend`.
   * *Streamlit*: `frontend/src/utils/api_client.py` posts JSON directly to the same FastAPI endpoints via `SARAL_API_BASE_URL` / `BACKEND_URL`.
3. **Intelligent Context Retrieval (RAG)**:
   * **Chat Mode**: Checks the query for document-related terms (e.g., "required papers", "certificate") and appends context terms (e.g., "income certificate proof") before executing a similarity search against Pinecone.
   * **Recommendation Mode**: Fires semantic queries, keyword queries, and national fallbacks in tandem. The results are unified and deduplicated based on text content signatures.
4. **Metadata Filtering (State Constraint Check)**: Discards chunks tied to mismatching state tags, securing precise location eligibility.
5. **Prompt Composition**: RAG Service or Recommendation Service formats the context excerpts, user attributes, and rules into an engineering prompt.
6. **Inference (Groq Cloud)**: Groq computes the prompt using `llama-3.3-70b-versatile` with `temperature=0.0` for maximum consistency.
7. **Post-Processing & Localisation**:
   * Extracts the JSON arrays using bracket-counting if extra conversation wraps the reply.
   * Standardizes and deduplicates recommendations based on prefix signatures (e.g., resolving sub-schemes to the parent scheme).
   * Generates localized output (e.g. Hindi, Tamil, Telugu, Gujarati, Marathi) based on the user's language selection.
8. **Dashboard Render**: The frontend parses the structured JSON payload, displays scheme recommendations as beautiful Cards, and appends chatbot answers to the scrolling message panel.