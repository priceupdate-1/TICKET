import json

from app.services.repository import JsonRepository
from app.services.seed import build_seed_data


COLLECTIONS = [
    "users",
    "userTypes",
    "roles",
    "departments",
    "systems",
    "categories",
    "areas",
    "teams",
    "tickets",
    "ticketNotes",
    "ticketStatusHistory",
    "ticketAttachments",
    "notifications",
    "auditLogs",
]


def _request_cache():
    """Return Flask's per-request `g` object if we're inside a request,
    else None. Lets us memoize Firestore reads per request without
    breaking script/CLI usage of the repository."""
    try:
        from flask import g, has_request_context
        if has_request_context():
            return g
    except (ImportError, RuntimeError):
        pass
    return None


class FirestoreRepository(JsonRepository):
    def __init__(self, credentials_path, project_id=None, credentials_json=None):
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
        except ImportError as error:
            raise RuntimeError("firebase-admin is not installed.") from error

        if not credentials_path and not credentials_json:
            raise RuntimeError(
                "Either FIREBASE_CREDENTIALS (path) or FIREBASE_CREDENTIALS_JSON (content) is required."
            )

        if not firebase_admin._apps:
            if credentials_json:
                try:
                    creds_dict = json.loads(credentials_json)
                except json.JSONDecodeError as error:
                    raise RuntimeError("FIREBASE_CREDENTIALS_JSON is not valid JSON.") from error
                cred = credentials.Certificate(creds_dict)
            else:
                cred = credentials.Certificate(credentials_path)

            if project_id:
                firebase_admin.initialize_app(cred, {"projectId": project_id})
            else:
                firebase_admin.initialize_app(cred)

        self.db = firestore.client()
        # Defer the seed/migration check to the first request so cold starts
        # don't burn quota or crash on RESOURCE_EXHAUSTED at import time.
        self._migrated = False

    def _ensure_migrated(self):
        if self._migrated:
            return
        try:
            from google.api_core import exceptions as gcp_exc
        except ImportError:
            gcp_exc = None
        try:
            if not self._has_required_seed():
                self._write(build_seed_data())
            else:
                self._ensure_schema()
            self._migrated = True
        except Exception as error:
            if gcp_exc and isinstance(error, gcp_exc.GoogleAPIError):
                raise RuntimeError(f"Firestore unavailable: {error}") from error
            raise

    def _read(self):
        cache = _request_cache()
        if cache is not None:
            cached = getattr(cache, "_firestore_data", None)
            if cached is not None:
                return cached
        data = self._fetch_all()
        if cache is not None:
            cache._firestore_data = data
        return data

    def _fetch_all(self):
        data = {}
        for collection_name in COLLECTIONS:
            data[collection_name] = [
                document.to_dict()
                for document in self.db.collection(collection_name).stream()
            ]
        data["userPermissions"] = {
            document.id: document.to_dict()
            for document in self.db.collection("userPermissions").stream()
        }
        counter_doc = self.db.collection("ticketCounters").document("default").get()
        data["ticketCounters"] = {
            "default": counter_doc.to_dict()
            if counter_doc.exists
            else build_seed_data()["ticketCounters"]["default"]
        }
        return data

    def _write(self, data):
        for collection_name in COLLECTIONS:
            for item in data.get(collection_name, []):
                document_id = item.get("id") or item.get("uid")
                if document_id:
                    self.db.collection(collection_name).document(document_id).set(item)

        for uid, permissions in data.get("userPermissions", {}).items():
            self.db.collection("userPermissions").document(uid).set(permissions)

        self.db.collection("ticketCounters").document("default").set(
            data.get("ticketCounters", {}).get("default", {})
        )

        cache = _request_cache()
        if cache is not None:
            cache._firestore_data = data

    # Collections that must all be non-empty for the app to be usable. If any
    # is empty (e.g. a partial seed where users got written but the lookup
    # tables didn't), treat the DB as needing seed and overwrite with the
    # build_seed_data() contents via _write() (which is an upsert, so any
    # existing user records are merged with the seed, not deleted).
    _SEED_REQUIRED_COLLECTIONS = (
        "users", "systems", "userTypes", "roles",
        "departments", "categories", "areas", "teams",
    )

    def _has_required_seed(self):
        for name in self._SEED_REQUIRED_COLLECTIONS:
            if not list(self.db.collection(name).limit(1).stream()):
                return False
        return True
