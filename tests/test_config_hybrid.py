import os
import sys

# Ensure backend can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from backend.app.core.config import settings

def test_config_loading():
    print("Locked & Loaded Configuration Test")
    print("-" * 30)

    pinecone_key = settings.PINECONE_API_KEY
    groq_key = settings.GROQ_API_KEY

    print(f"PINECONE_API_KEY present: {bool(pinecone_key)}")
    print(f"GROQ_API_KEY present: {bool(groq_key)}")

    # Check OS Environ Injection (Critical for LangChain)
    print(f"os.environ['PINECONE_API_KEY'] present: {bool(os.environ.get('PINECONE_API_KEY'))}")

    if pinecone_key and os.environ.get("PINECONE_API_KEY") == pinecone_key:
        print("SUCCESS: Keys loaded and injected into environment.")
    else:
        print("FAILURE: Keys missing or not injected.")

if __name__ == "__main__":
    test_config_loading()
