"""
RAG retriever service – fetches semantically relevant context
from a Pinecone vector store for use in LLM prompts.
"""

import re

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

from backend.app.core.config import settings

# Keywords that signal the user is asking about required documents
_DOC_KEYWORDS = re.compile(
    r"\b(document|paper|proof|certificate|enclosure|attach|kagaz|dastavez|pramaan)\b",
    re.IGNORECASE,
)

# Extra terms appended to the query when document keywords are detected
_DOC_EXPANSION = (
    " list of required documents aadhaar card income certificate"
    " caste certificate residency proof eligibility criteria"
    " required enclosures application form"
)


class RAGService:
    """Retrieve relevant document chunks from Pinecone via similarity search."""

    def __init__(self) -> None:
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=self.embeddings,
            pinecone_api_key=settings.PINECONE_API_KEY,
        )

    @staticmethod
    def _expand_query(query: str) -> str:
        """If the query mentions documents/proof, append extra search terms."""
        if _DOC_KEYWORDS.search(query):
            expanded = query + _DOC_EXPANSION
            print(f"DEBUG [RAGService]: query expanded to {expanded!r}")
            return expanded
        return query

    def get_context(self, query: str, k: int = 5, filters: dict = None) -> str:
        """Return the top-k most relevant chunks joined by double newlines.

        Args:
            query: The search query string.
            k: Number of top results to retrieve.
            filters: Optional metadata filter dict passed to Pinecone.
        """
        search_query = self._expand_query(query)
        print(f"DEBUG [RAGService]: query={search_query!r}, k={k}, filters={filters}")
        docs = self.vector_store.similarity_search(search_query, k=k, filter=filters)
        print(f"DEBUG [RAGService]: retrieved {len(docs)} documents")
        return "\n\n".join(doc.page_content for doc in docs)

    def get_raw_docs(self, query: str, k: int = 50, filters: dict | None = None):
        """Return raw Document objects from similarity search.

        Args:
            query: search string.
            k: number of results.
            filters: optional Pinecone metadata filter applied **server-side**
                (e.g. ``{"$or": [{"level": {"$eq": "Central"}}, ...]}``).

        Returning raw Documents lets the caller inspect metadata and apply
        any remaining application-level logic (re-ranking, safety nets).
        """
        search_query = self._expand_query(query)
        print(f"DEBUG [RAGService]: broad search query={search_query!r}, k={k}, filters={filters}")
        docs = self.vector_store.similarity_search(search_query, k=k, filter=filters)
        print(f"DEBUG [RAGService]: retrieved {len(docs)} raw documents")
        return docs
