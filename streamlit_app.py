import os
import sys

# 1. Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# 2. Set Cloud Environment Flag
# This tells api_client.py to use direct backend imports
os.environ["DEPLOYMENT_ENV"] = "CLOUD"

# 3. Import and run the main frontend app
from frontend import app

if __name__ == "__main__":
    # creating a dummy context if needed or just letting app run
    pass
