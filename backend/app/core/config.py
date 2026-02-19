import os
from dotenv import load_dotenv

# Load local .env if it exists
load_dotenv()

def get_secret(key_name: str) -> str:
    # 1. Try OS Environment Variables (.env via load_dotenv)
    value = os.getenv(key_name)
    if value:
        return value

    # 2. Fallback to Streamlit Secrets (Cloud)
    try:
        import streamlit as st
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
        
    return None

class Settings:
    """
    Configuration provider that ensures keys are available in os.environ
    for libraries like LangChain, regardless of source (.env or st.secrets).
    """
    def __init__(self):
        # Explicitly fetch and inject into os.environ
        self._ensure_env("PINECONE_API_KEY")
        self._ensure_env("GROQ_API_KEY")
        
        # Load other settings
        self.PINECONE_ENV = get_secret("PINECONE_ENV")
        self.PINECONE_INDEX_NAME = get_secret("PINECONE_INDEX_NAME") or "bharat-schemes"

    def _ensure_env(self, key: str):
        val = get_secret(key)
        if val:
            os.environ[key] = val
            setattr(self, key, val)
        else:
            # We don't crash here; let the consumer fail if they need it.
            setattr(self, key, None)

# Global singleton
settings = Settings()
