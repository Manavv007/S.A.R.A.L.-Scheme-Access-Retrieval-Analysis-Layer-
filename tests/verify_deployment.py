import os
import sys

# 1. Simulate the path setup from app.py
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

print(f"Project Root: {PROJECT_ROOT}")

# 2. Simulate Cloud Environment
os.environ["DEPLOYMENT_ENV"] = "CLOUD"

try:
    # 3. Import api_client which should trigger backend imports
    from frontend.src.utils.api_client import get_chat_response, get_recommendations
    print("✅ Successfully imported api_client in CLOUD mode.")
    
    # 4. Check if backend modules are actually loaded
    import sys
    if "backend.app.services.rag_retriever" in sys.modules:
        print("✅ Backend services loaded into sys.modules.")
    else:
        print("⚠️ Backend services NOT loaded (Did the import logic run?)")

except ImportError as e:
    print(f"❌ ImportError during verification: {e}")
except Exception as e:
    print(f"❌ General Error during verification: {e}")
