import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-this-secret")
    APP_NAME = os.environ.get("APP_NAME", "KG Ticket Control")
    STORAGE_MODE = os.environ.get("APP_STORAGE_MODE", "local")
    AUTH_PROVIDER = os.environ.get("AUTH_PROVIDER", "local")
    LOCAL_STORE_PATH = Path(os.environ.get("LOCAL_STORE_PATH", BASE_DIR / "data" / "phase1_store.json"))
    FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
    # Either a path to a service account JSON file (FIREBASE_CREDENTIALS)
    # OR the JSON content itself in an env var (FIREBASE_CREDENTIALS_JSON)
    # The JSON env var is preferred for Vercel / Render since their filesystems are ephemeral.
    FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS", "")
    FIREBASE_CREDENTIALS_JSON = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")
    FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")
