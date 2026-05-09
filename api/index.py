"""Vercel Python entrypoint.

Vercel auto-discovers handlers under /api. This file exposes the Flask `app`
as `app` so `@vercel/python` can serve it as a WSGI application.
"""
import os
import sys
from pathlib import Path

# Make the project root importable so `from app import create_app` works.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from app import create_app  # noqa: E402

app = create_app()
