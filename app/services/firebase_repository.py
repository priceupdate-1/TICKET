import json
import time
from copy import deepcopy

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

# Lookups change rarely (only via admin actions). Cache them across requests
# in this Python process with a short TTL. A write that touches any of these
# collections clears the cache so admins see their changes immediately.
_LOOKUP_COLLECTIONS = (
    "systems", "categories", "areas", "teams",
    "userTypes", "roles", "departments",
)
# Everything else is fetched fresh per request (still memoized within the
# request via Flask's `g`).
_VOLATILE_COLLECTIONS = (
    "users", "tickets", "ticketNotes", "ticketStatusHistory",
    "ticketAttachments", "notifications", "auditLogs",
)

_LOOKUP_CACHE = {"data": None, "ts": 0.0}
_LOOKUP_TTL_SECONDS = 300


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
            # Snapshot pre-mutation state so _write can compute deltas and
            # only push the documents that actually changed.
            cache._firestore_snapshot = deepcopy(data)
        return data

    def _fetch_all(self):
        # Lookups: process-wide TTL cache. Deep-copy on return so callers can
        # mutate freely without poisoning the cache.
        now = time.time()
        cache = _LOOKUP_CACHE
        if cache["data"] is None or (now - cache["ts"]) >= _LOOKUP_TTL_SECONDS:
            cache["data"] = self._fetch_lookups_fresh()
            cache["ts"] = now
        data = deepcopy(cache["data"])

        # Volatile collections: always fetch fresh (per-request memoization
        # in _read() handles repeats within one request).
        for name in _VOLATILE_COLLECTIONS:
            data[name] = [doc.to_dict() for doc in self.db.collection(name).stream()]

        counter_doc = self.db.collection("ticketCounters").document("default").get()
        data["ticketCounters"] = {
            "default": counter_doc.to_dict()
            if counter_doc.exists
            else build_seed_data()["ticketCounters"]["default"]
        }
        return data

    def _fetch_lookups_fresh(self):
        data = {}
        for name in _LOOKUP_COLLECTIONS:
            data[name] = [doc.to_dict() for doc in self.db.collection(name).stream()]
        data["userPermissions"] = {
            doc.id: doc.to_dict() for doc in self.db.collection("userPermissions").stream()
        }
        return data

    def _write(self, data):
        cache = _request_cache()
        snapshot = getattr(cache, "_firestore_snapshot", None) if cache is not None else None
        if snapshot is None:
            self._write_all(data)
        else:
            self._write_delta(snapshot, data)
        if cache is not None:
            cache._firestore_data = data
            cache._firestore_snapshot = deepcopy(data)

    def _write_all(self, data):
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
        # Lookups were just written -- next request must refetch.
        _LOOKUP_CACHE["data"] = None

    def _write_delta(self, old, new):
        """Write only the documents that actually changed between old and new.
        Soft-deletes are honoured (the isDeleted=True item is still in `new`);
        we intentionally do NOT delete docs that disappear from `new` so a
        partial in-memory list never wipes Firestore data."""
        lookups_changed = False
        for name in COLLECTIONS:
            old_items = {
                (it.get("id") or it.get("uid")): it
                for it in old.get(name, []) or []
                if (it.get("id") or it.get("uid"))
            }
            new_items = {
                (it.get("id") or it.get("uid")): it
                for it in new.get(name, []) or []
                if (it.get("id") or it.get("uid"))
            }
            for doc_id, item in new_items.items():
                if old_items.get(doc_id) != item:
                    self.db.collection(name).document(doc_id).set(item)
                    if name in _LOOKUP_COLLECTIONS:
                        lookups_changed = True

        old_perms = old.get("userPermissions", {}) or {}
        new_perms = new.get("userPermissions", {}) or {}
        for uid, perm in new_perms.items():
            if old_perms.get(uid) != perm:
                self.db.collection("userPermissions").document(uid).set(perm)
                lookups_changed = True

        old_counter = (old.get("ticketCounters") or {}).get("default")
        new_counter = (new.get("ticketCounters") or {}).get("default")
        if new_counter and new_counter != old_counter:
            self.db.collection("ticketCounters").document("default").set(new_counter)

        if lookups_changed:
            _LOOKUP_CACHE["data"] = None

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
