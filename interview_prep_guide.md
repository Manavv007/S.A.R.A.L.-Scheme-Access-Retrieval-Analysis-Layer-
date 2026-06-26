# S.A.R.A.L. - Infosys SP L1 Interview Preparation Guide

This is your master preparation document for the Infosys Specialist Programmer (SP) L1 interview, tailored *exactly* to your S.A.R.A.L. (Scheme Access Retrieval Analysis Layer) codebase.

---

## 1. PROJECT OVERVIEW

### What is S.A.R.A.L? What problem does it solve? Why did I build this?
**What the code does:** S.A.R.A.L is an AI-powered Government Scheme Advisor. It takes a user profile (age, occupation, state, income, caste, language) in `backend/app/models/dtos.py` (`UserProfile`) and matches it against government scheme guidelines using a RAG pipeline (`RAGService` in `rag_retriever.py`).

**Interview Answer:**
> "I built S.A.R.A.L., which stands for Scheme Access Retrieval Analysis Layer. The gap in the market I noticed is that while the Indian government has thousands of welfare schemes, average citizens—especially farmers or daily wage workers—don't know what they are eligible for. The criteria are buried in complex, 50-page PDF documents. I built S.A.R.A.L to solve this. It takes basic user details like age, income, state, and occupation, and uses a Retrieval-Augmented Generation (RAG) pipeline to search through official scheme documents and tell the user exactly what they qualify for, in their native language."

**Follow-up Questions:**
- **Q: How do you ensure the information is accurate and not hallucinated?**
  - *A:* "I rely on strict RAG. In my `_ELIGIBILITY_PROMPT` inside `recommendation.py`, I explicitly tell the LLM to 'Identify ALL schemes from the above context' and if the answer isn't in the context, to say it doesn't have enough information. I also implemented a strict Metadata Filter before the LLM even sees the context to drop documents belonging to different states."
- **Q: What was the biggest challenge you faced building this?**
  - *A:* "Handling complex eligibility logic. Financial numbers and intersecting criteria (like caste + income + occupation) are hard for basic semantic search. To solve this, I built a hybrid retrieval engine in `recommendation.py` that runs 3 parallel strategies (Semantic, Keyword, and National fallback) and strictly filters out incorrect states before passing it to the LLM."

### What is the overall architecture? What does each file/folder do?
**What the code does:** The architecture is a decoupled Monolith (currently running in Cloud deployment mode). Frontend is Streamlit (`frontend/app.py`), backend is FastAPI (`backend/app/main.py`). The core brain is in `backend/app/services/` (`llm_engine.py`, `rag_retriever.py`, `recommendation.py`).

**Interview Answer:**
> "The architecture is cleanly separated into two main layers. On the frontend, I used Streamlit (`frontend/app.py`) for a rapid, responsive UI. It talks to my backend layer, which is built with FastAPI. The backend is modular. Inside `backend/app/services`, I have `rag_retriever.py` connecting to Pinecone, `llm_engine.py` connecting to Groq's Llama-3, and `recommendation.py` which orchestrates the logic. For data ingestion, I wrote separate Python scripts like `ingest_pdfs.py` to chunk and upsert data into the vector database."

### Key Design Decisions and WHY
**Interview Answer:**
> "A few key decisions stand out. First, **Separation of Concerns**: Even though I can call Pinecone directly from Streamlit, I built a dedicated FastAPI backend and `services` layer. This makes the app production-ready and allows me to swap out the UI for React or a mobile app later without touching the core logic. Second, **Hybrid Search Logic**: In `recommendation.py`, I don't just do one similarity search. I do three parallel queries: a semantic query, a keyword query, and a national fallback query, then deduplicate them. This drastically improves recall for complex edge cases."

---

## 2. RAG PIPELINE (Crucial Section)

### How does the ingestion pipeline work? What loaders and chunking?
**What the code does:** In `backend/scripts/ingest_pdfs.py`, it uses `PyPDFLoader`, `CSVLoader`, and `TextLoader`. It uses `RecursiveCharacterTextSplitter` with `chunk_size=1000` and `chunk_overlap=200`. It extracts the `state` from the parent folder name and tags it in metadata.

**Interview Answer:**
> "My ingestion pipeline is in `ingest_pdfs.py`. I loop through my `data/raw_pdfs` directory recursively. Depending on the file extension, I dynamically choose the right LangChain document loader—`PyPDFLoader` for PDFs, `CSVLoader` for data, and `TextLoader` for text or JSON. 
> 
> For chunking, I used LangChain's `RecursiveCharacterTextSplitter`. I chose a `chunk_size` of 1000 characters with an `overlap` of 200. I found 1000 characters is a sweet spot—it's large enough to capture complete sentences about eligibility criteria, but small enough to fit many chunks into the LLM context window. The 200-character overlap ensures I don't cut a crucial income limit sentence in half."

**Follow-up Questions:**
- **Q: How did you handle metadata during ingestion?**
  - *A:* "Smart tagging. I set up my folders by state. During ingestion, the script reads the parent folder name and injects it as `doc.metadata['state']`. This is critical for the recommendation engine later so it can filter out Maharashtra schemes for a Gujarat user."

### How are embeddings generated and upserted?
**What the code does:** Uses `HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")` and `PineconeVectorStore.from_documents`.

**Interview Answer:**
> "I used HuggingFace's `all-MiniLM-L6-v2` model for embeddings. I chose this because it's extremely fast, lightweight, and produces 384-dimensional vectors, which keeps Pinecone storage costs low while maintaining high semantic accuracy. I instantiate the `HuggingFaceEmbeddings` class, chunk the documents, and use `PineconeVectorStore.from_documents` to batch upsert the vectors and metadata directly into my Pinecone index."

### How does retrieval work? What is top-k? What similarity metric?
**What the code does:** In `rag_retriever.py`, `similarity_search` is used. By default, it uses cosine similarity (configured on the Pinecone index side, standard for MiniLM). For general chat it retrieves `k=5`, but for recommendations (`recommendation.py`), it does 3 searches retrieving `k=10`, `k=10`, and `k=15`, combining and deduplicating them.

**Interview Answer:**
> "For retrieval, the process changes based on the endpoint. For simple chat queries in `rag_retriever.py`, I retrieve the top 5 most similar chunks. But for the core recommendation engine, I implemented a custom multi-vector search. I execute three parallel similarity searches—a semantic query, a keyword-focused query, and a national scheme fallback query—pulling between 10 to 15 chunks each. I then programmatically deduplicate them using a content signature. This ensures I don't miss anything. The similarity metric is Cosine Similarity, which is standard for the MiniLM embeddings I used."

**Follow-up Questions:**
- **Q: You mentioned expanding queries. How did you do that?**
  - *A:* "In `rag_retriever.py`, I built a regex check `_DOC_KEYWORDS`. If the user asks about 'documents' or 'proof', I automatically append extra keywords like 'aadhaar card income certificate' to the query before sending it to Pinecone. This forces the vector DB to return chunks containing document lists."

### How is the final answer generated? Prompt templates?
**What the code does:** In `recommendation.py`, you use `_ELIGIBILITY_PROMPT` containing variables `{profile}`, `{context}`, `{user_occupation}`, `{user_income}`, `{negative_constraint}`, and `{language}`.

**Interview Answer:**
> "Once I have the deduplicated and state-filtered context chunks, I inject them into a highly engineered prompt in `recommendation.py` called `_ELIGIBILITY_PROMPT`. I pass the user's JSON profile, occupation, and income explicitly. 
> 
> The prompt uses Chain-of-Thought style instructions. I give the LLM strict 'Step 1' and 'Step 2' logic for occupation and income filtering. I instruct the LLM to output ONLY a JSON array with `scheme_name`, `eligibility_status`, and a `reason` translated into the user's requested language. I then invoke my `LLMEngine` which passes this to Groq's LLaMA-3."

**Follow-up Questions:**
- **Q: What happens when the LLM hallucinates JSON formatting?**
  - *A:* "I wrote a custom `_parse_response` method. It tries a standard `json.loads` first. If that fails, it uses a bracket-counting algorithm (`_extract_json_array`) to find the first balanced JSON array inside the raw text. If even that fails, it gracefully falls back by wrapping the raw text in a default dictionary structure."

---

## 3. LANGCHAIN INTERNALS

### Which LangChain components did I use?
**What the code does:** You used `ChatGroq`, `PromptTemplate`, `StrOutputParser`, `HuggingFaceEmbeddings`, `PineconeVectorStore`, `RecursiveCharacterTextSplitter`, `PyPDFLoader`, `CSVLoader`, `TextLoader`.

**Interview Answer:**
> "I heavily utilized LangChain's ecosystem to standardize my pipeline. I used their Document Loaders and `RecursiveCharacterTextSplitter` for data prep. For the vector store, I used `langchain_pinecone.PineconeVectorStore`, and for embeddings, `langchain_huggingface.HuggingFaceEmbeddings`. 
> 
> For the orchestration, I used LangChain Expression Language (LCEL). In my `llm_engine.py`, my chain is defined simply as `self.chain = self.prompt | self.llm | self.parser`. This creates a very clean, readable pipeline connecting my `PromptTemplate`, `ChatGroq` model, and `StrOutputParser`."

### How does memory work?
**What the code does:** You implemented conversation history manually. In `llm_engine.py`, it takes a `history` list from the frontend, loops through the last 10 messages, formats them as `User:` and `AI:`, and prepends them to the current query.

**Interview Answer:**
> "Instead of using LangChain's heavy memory classes like `ConversationBufferMemory`, I implemented custom history management to maintain stateless API endpoints. The Streamlit frontend stores the chat history in `st.session_state`. When a user sends a chat, the frontend passes the history array to the backend. In `llm_engine.py`, I slice the last 10 messages to prevent token overflow, format them into a 'Previous conversation' block, and prepend it to the current user query. This allows the LLM to understand context statelessly."

---

## 4. PINECONE & VECTOR DATABASE

### How is Pinecone configured and connected?
**What the code does:** Connected via API key and index name in environment variables. `settings.PINECONE_INDEX_NAME` defaults to `bharat-schemes`.

**Interview Answer:**
> "I used Pinecone Serverless for my vector database. It's configured via environment variables—I pass `PINECONE_API_KEY` and the index name `bharat-schemes` to the `PineconeVectorStore` class. Pinecone manages the dimensions (384 for MiniLM) and the cosine similarity metric automatically based on index creation settings. I chose Pinecone over FAISS or ChromaDB because I wanted a fully managed, cloud-native database that scales without me having to manage persistent volumes or Docker disk storage in my CI/CD pipeline."

### How are vectors upserted and queried?
**What the code does:** Vectors are upserted immediately file-by-file in `ingest_pdfs.py` using `PineconeVectorStore.from_documents()`. They are queried using `.similarity_search()` or `.similarity_search_with_score()`.

**Interview Answer:**
> "In my ingestion script, I chunk the documents and immediately call `PineconeVectorStore.from_documents()`. This acts as an upsert batch operation. For querying, I use the `similarity_search` method. A critical part of my querying logic is Metadata Filtering. In `recommendation.py`, I pull raw documents from Pinecone using `get_raw_docs`, and then I strictly filter them based on the `state` metadata tag to ensure users only see schemes relevant to their location."

---

## 5. EMBEDDINGS

### Which model and why?
**What the code does:** `HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")`

**Interview Answer:**
> "I specifically chose the `all-MiniLM-L6-v2` model from HuggingFace via SentenceTransformers. It outputs vectors with 384 dimensions. I chose this over OpenAI's `text-embedding-ada-002` (which is 1536 dimensions) because MiniLM is open-source, runs fast locally without network latency, and the smaller dimensionality drastically reduces the storage and query costs on Pinecone while still providing excellent semantic matching for English scheme documents."

---

## 6. STREAMLIT UI

### How does it work and communicate with backend?
**What the code does:** `frontend/app.py` has a sidebar form for profile, session state for storing profile/messages/recommendations. Uses `api_client.py` which dynamically imports backend classes (if `CLOUD` mode) or makes HTTP requests. Custom CSS is injected via `st.markdown(unsafe_allow_html=True)`.

**Interview Answer:**
> "The UI is built in Streamlit. I designed it to feel like a premium SaaS dashboard by injecting custom CSS to override Streamlit's default look, giving it a modern dark theme and card-based layouts. 
> 
> State is managed via `st.session_state` to store the user's profile, chat history, and recommendations across reruns. 
> 
> For backend communication, I built an `api_client.py`. Because I deployed this on Hugging Face Spaces, I set a `DEPLOYMENT_ENV='CLOUD'` flag. When this flag is active, instead of making HTTP requests to a local FastAPI server, the Streamlit app dynamically imports my backend services (`RecommendationService`, `LLMEngine`) and runs the Python functions directly. This creates a highly efficient monolith for cloud deployment while keeping the code perfectly modular for local microservice development."

---

## 7. CI/CD (GITHUB ACTIONS)

### What does the workflow do?
**What the code does:** `.github/workflows/sync_to_hf.yml` runs on `push` to `main`. It checks out the code, deletes `.git` history, deletes raw PDFs, creates a fresh 1-commit git history, and force-pushes to the Hugging Face Space repository using an `HF_TOKEN`.

**Interview Answer:**
> "My CI/CD pipeline is handled by GitHub Actions. Whenever I push to the `main` branch, the `sync_to_hf.yml` workflow triggers. Its main job is to deploy the app to Hugging Face Spaces. 
> 
> Interestingly, I had to implement a custom step because Hugging Face limits repository sizes. In my pipeline, I checkout the code, physically delete the `data/raw_pdfs` folder and the `.git` directory to wipe the memory of large files. I then initialize a brand new, clean git repository, commit the lightweight code, and perform a force push to the Hugging Face remote using a secret `HF_TOKEN`. This ensures my deployment is always lightweight and fast."

---

## 8. ERROR HANDLING & EDGE CASES

### What happens when an API fails?
**What the code does:** Try/except blocks in `app.py` and `api_client.py`. Displays `st.error()` or `st.warning()`. JSON extraction fallback in `recommendation.py`.

**Interview Answer:**
> "I built multi-layered error handling. At the API level (FastAPI), I wrap endpoints in `try/except` blocks and return 500 HTTP exceptions with details. In `api_client.py`, if the Groq LLM API times out or fails, I catch the exception, populate a `debug_info` dictionary, and return `None` for the response. 
> 
> On the Streamlit frontend, if `result is None`, I capture the error from `debug_info` and display a graceful `st.error` alert to the user rather than letting the app crash. 
> 
> The most critical error handling is for the LLM output. If Groq ignores my instructions and returns conversational text instead of raw JSON, my custom `_parse_response` function steps in, extracts the JSON array using bracket counting, or wraps the raw text in a default fallback scheme format. This guarantees the UI never breaks trying to render the cards."

---

## 9. PERFORMANCE & SCALABILITY

### What are the bottlenecks? How to scale to 10k users?
**Interview Answer:**
> "Currently, the main bottleneck is the LLM generation time. Groq is incredibly fast, but the RAG retrieval + LLM analysis takes a few seconds.
> 
> To scale to 10,000 concurrent users, I would make three major architectural changes:
> 1. **Decouple the Monolith**: I'd move from the current 'Cloud' direct-import mode to deploying the FastAPI backend to an AWS ECS cluster with an Application Load Balancer, and host the frontend on Vercel or CloudFront.
> 2. **Implement Caching**: I would add Redis. Many users have identical profiles (e.g., 'Student, Gujarat, 1 Lakh Income'). If a profile hash already exists in Redis, I can return the cached JSON response instantly without hitting Pinecone or Groq.
> 3. **Async Processing**: Ensure all FastAPI endpoints and Pinecone/Groq SDK calls utilize Python's `async/await` perfectly to prevent blocking the event loop under heavy load."

---

## 10. ALTERNATIVES & TRADE-OFFS (Hardest Questions)

### Why RAG over fine-tuning?
**Interview Answer:**
> "Fine-tuning bakes knowledge into the model weights, which is expensive and makes it impossible to update dynamically. Government schemes change frequently (new income limits, new deadlines). With RAG, if a scheme updates, I just delete a vector and upsert a new chunk into Pinecone. The LLM acts purely as a reasoning engine, not a database."

### Why Llama-3 (Groq) over OpenAI?
**Interview Answer:**
> "I chose Llama-3 via Groq primarily for speed. Groq's LPU architecture provides blazingly fast inference, often over 300 tokens per second. For a UI where users are waiting for multiple scheme recommendations, latency is critical. Plus, Llama-3 70B is open-source and highly capable of the complex reasoning required for my eligibility logic, matching GPT-4's performance at a fraction of the cost."

### What would you do differently today?
**Interview Answer:**
> "If I started over today, I would implement **GraphRAG**. Standard semantic search sometimes struggles with complex relational data (like 'Scheme A is a sub-scheme of Scheme B'). Using a knowledge graph combined with vectors would allow the system to map exactly how occupations, castes, and ministries connect to schemes, making the retrieval step virtually flawless."

---

## 11. METRICS, EVALUATION & SECURITY

### How do you measure accuracy?
**Interview Answer:**
> "Currently, accuracy is managed via strict prompting and metadata filtering. However, for a production system, I would integrate the **RAGAS framework** (Retrieval Augmented Generation Assessment). I'd measure 'Faithfulness' (did the LLM hallucinate beyond the context?) and 'Context Precision' (did Pinecone return the right chunks?)."

### Security & API Keys
**What the code does:** `.env` file, `config.py` uses `load_dotenv` and Streamlit `st.secrets`. `gitignore` ignores `.env`.

**Interview Answer:**
> "Security is handled primarily through environment variable isolation. My `.env` file is in `.gitignore`, so keys are never exposed in GitHub. In `core/config.py`, I built a robust settings loader that first checks OS environment variables, and falls back to Streamlit's `st.secrets` manager for cloud deployments. I also manually inject the keys into `os.environ` to ensure LangChain's internal classes pick them up securely without me having to hardcode them anywhere in the architecture."
