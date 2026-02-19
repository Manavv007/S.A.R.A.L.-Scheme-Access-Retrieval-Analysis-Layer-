import sys
import os

# 1. Dynamically add the project root to the Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 2. Set Cloud Environment Flag
os.environ["DEPLOYMENT_ENV"] = "CLOUD"

# 3. Import and run the main frontend app
from frontend import app
