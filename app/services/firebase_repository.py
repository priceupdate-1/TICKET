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
    "auditLogs",
]


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
        if not self._has_required_seed():
            self._write(build_seed_data())
        else:
            self._ensure_schema()

    def _read(self):
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

    def _has_required_seed(self):
        return bool(list(self.db.collection("users").limit(1).stream()))
