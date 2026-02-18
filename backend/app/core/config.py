import os

# Try to import streamlit to access secrets. 
# If running in FastAPI (uvicorn) without streamlit installed/active, this might fail or be unused.
try:
    import streamlit as st
except ImportError:
    st = None

class Settings:
    """
    Configuration provider that prioritizes Streamlit Secrets (for Cloud)
    and falls back to Environment Variables (for Local/Docker).
    """
    
    def _get_val(self, key: str) -> str:
        # 1. Try Streamlit Secrets
        if st is not None:
            try:
                # st.secrets behaves like a dict
                if key in st.secrets:
                    val = st.secrets[key]
                    if val: return val
            except Exception:
                # Running outside Streamlit context
                pass
        
        # 2. Fallback to System Environment (os.getenv)
        return os.getenv(key, "")

    @property
    def GROQ_API_KEY(self) -> str:
        return self._get_val("GROQ_API_KEY")

    @property
    def PINECONE_API_KEY(self) -> str:
        return self._get_val("PINECONE_API_KEY")

    @property
    def PINECONE_ENV(self) -> str:
        return self._get_val("PINECONE_ENV")

    @property
    def PINECONE_INDEX_NAME(self) -> str:
        return self._get_val("PINECONE_INDEX_NAME")

# Global singleton
settings = Settings()
