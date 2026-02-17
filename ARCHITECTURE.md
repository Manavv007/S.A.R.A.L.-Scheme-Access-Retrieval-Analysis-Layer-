bharat-scheme-ai/
├── backend/                  # The Intelligence Layer (Python/FastAPI)
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── chat.py           # Endpoints for chat streaming
│   │   │   │   ├── schemes.py        # Endpoints for searching schemes
│   │   │   │   └── admin.py          # Endpoints for triggering ingestion
│   │   ├── core/
│   │   │   ├── config.py             # Env variables (Pydantic BaseSettings)
│   │   │   └── security.py           # API Key validation (if needed)
│   │   ├── services/                 # PURE BUSINESS LOGIC (The Brain)
│   │   │   ├── llm_engine.py         # Groq/Llama-3 interactions
│   │   │   ├── rag_retriever.py      # Pinecone query logic & hybrid search
│   │   │   ├── pdf_parser.py         # Advanced chunking logic (Recursive)
│   │   │   └── recommendation.py     # Logic to match User Profile <-> Scheme
│   │   ├── models/
│   │   │   ├── dtos.py               # Pydantic models (Request/Response bodies)
│   │   │   └── db_schemas.py         # Database models (if using SQL later)
│   │   └── main.py                   # FastAPI entry point
│   ├── scripts/                      # OPS scripts (Run these manually or via Cron)
│   │   ├── ingest_pdfs.py            # The "Loader" script
│   │   ├── reset_db.py               # Wipes Pinecone index (Careful!)
│   │   └── test_groq.py              # Quick connection test
│   ├── tests/                        # Pytest folder
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                 # The User Layer (Streamlit now, React later)
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat_interface.py     # Reusable Chat UI component
│   │   │   ├── scheme_card.py        # Reusable Card UI component
│   │   │   └── sidebar_profile.py    # Reusable Profile Form
│   │   ├── pages/
│   │   │   ├── 1_Advisor.py          # Main Chat Page
│   │   │   └── 2_Dashboard.py        # Admin/Stats Page
│   │   └── utils/
│   │       └── api_client.py         # Python wrapper to call Backend API
│   ├── assets/                       # Images/Logos
│   └── app.py                        # Streamlit Entry Point
│
├── n8n-workflows/            # The Automation Layer
│   ├── workflow_whatsapp.json        # Import into n8n: Sends WhatsApp msg
│   ├── workflow_email_check.json     # Import into n8n: Sends Email list
│   └── workflow_db_sync.json         # (Optional) Syncs Google Sheets -> DB
│
├── data/                     # The Knowledge Base
│   ├── raw_pdfs/                     # Dump government PDFs here
│   ├── processed/                    # JSONs of parsed text (debug)
│   └── templates/                    # HTML/Jinja2 templates for "Auto-Filling" forms
│
├── docs/                     # Documentation
│   ├── API_SPEC.md
│   └── DEPLOYMENT_GUIDE.md
│
├── .env.example
├── docker-compose.yml        # Orchestrate Backend + Frontend + Vector DB (local)
└── README.md