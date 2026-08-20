import os
import sys

# Add the root directory to the Python path so we can import app.py and ml modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
