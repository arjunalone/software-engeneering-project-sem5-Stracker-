import os
import sys

# Ensure project root is on sys.path so 'backend' package can be imported
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend import create_app  # noqa: E402

# WSGI entrypoint for Flask
app = create_app()
