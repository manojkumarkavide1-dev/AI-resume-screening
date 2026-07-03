import sys
import os

# Resolve the backend directory relative to this file and add to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, os.path.normpath(backend_dir))

from app import app
