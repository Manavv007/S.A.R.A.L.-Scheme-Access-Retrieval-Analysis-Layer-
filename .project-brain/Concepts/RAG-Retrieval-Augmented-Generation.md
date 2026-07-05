---
type: concept
project: S.A.R.A.L.
status: active
confidence: confirmed
created: 2026-07-05
related:
  - "[[System-Overview]]"
  - "[[Eligibility-Engine]]"
  - "[[Ingestion-Scraper]]"
  - "[[Researcher-Critic-Relevance-Loop]]"
  - "[[MiniLM-Candidate-Reranking]]"
---

# Retrieval-Augmented Generation (RAG)

## 1. What is S.A.R.A.L.'s RAG Concept?
S.A.R.A.L. is fundamentally a **RAG-based application**. Instead of expecting the LLM to memorize all Indian welfare schemes (which leads to hallucinations and outdated recommendations), scheme guidelines are scraped, embedded, stored in a vector database, and retrieved dynamically when a user submits their profile.

---

## 2. Ingestion Flow
1. **Scraping:** Spiders fetch raw documents from portals.
2. **Chunking:** Documents are split into 1000-character segments.
3. **Embedding:** Segments are converted into 384-dimensional dense vectors using a local HuggingFace `all-MiniLM-L6-v2` embeddings pipeline.
4. **Vector Store:** Vectors are uploaded to the Pinecone index (`bharat-schemes`).
* *Detail Component:* see **[[Ingestion-Scraper]]**.

---

## 3. Query & Retrieval Flow
When a user profile is submitted:
1. **Multi-Vector Search:** Three queries (semantic, state-based, national) retrieve up to 40 candidate chunks.
2. **State Constraint Filtering:** Checks match categories server-side.
3. **Researcher-Critic Loop:** Evaluates snippet topic relevance, refining search terms up to 3 times.
4. **Re-Ranking:** Selects top 15 candidates based on local cosine similarity scores.
5. **LLM Synthesis:** Groq (`llama-3.3-70b-versatile`) evaluates rules and formats output.
* *Detail Component:* see **[[Eligibility-Engine]]**.

---

## 4. Why This Concept Matters
Standard search algorithms match keywords but miss semantic context. RAG resolves this by pairing high-dimensional concept similarity with deterministic LLM evaluation, allowing S.A.R.A.L. to extract details from complex government policies accurately.
