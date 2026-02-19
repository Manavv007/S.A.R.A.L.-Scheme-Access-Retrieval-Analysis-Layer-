import sys
import os

# 1. Dynamically add the project root to the Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 2. Add 'frontend' to sys.path so 'from src.utils' works in frontend/app.py
frontend_dir = os.path.join(root_dir, "frontend")
if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)

# 3. Set Cloud Environment Flag
os.environ["DEPLOYMENT_ENV"] = "CLOUD"

# 4. Import and run the main frontend app
from frontend import app
