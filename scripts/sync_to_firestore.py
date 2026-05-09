"""Upload the local JSON store to Firestore.

Usage:
    python scripts/sync_to_firestore.py
    python scripts/sync_to_firestore.py --force   # overwrite even if Firestore already has data
    python scripts/sync_to_firestore.py --source data/phase1_store.json

Env vars (read from .env or environment):
    FIREBASE_PROJECT_ID         - the project (e.g. kg-ticket)
    FIREBASE_CREDENTIALS_JSON   - service-account JSON content (preferred for CI/cloud)
    FIREBASE_CREDENTIALS        - path to a service-account JSON file (alternative)
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    print("python-dotenv not installed — relying on real env vars.")

import firebase_admin
from firebase_admin import credentials, firestore


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


def init_firestore():
    project_id = os.environ.get("FIREBASE_PROJECT_ID", "").strip()
    creds_json = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()
    creds_path = os.environ.get("FIREBASE_CREDENTIALS", "").strip()

    if not project_id:
        sys.exit("FIREBASE_PROJECT_ID is required (set it in .env)")

    if creds_json:
        try:
            cred = credentials.Certificate(json.loads(creds_json))
        except json.JSONDecodeError as e:
            sys.exit(f"FIREBASE_CREDENTIALS_JSON is not valid JSON: {e}")
    elif creds_path:
        if not Path(creds_path).exists():
            sys.exit(f"FIREBASE_CREDENTIALS file not found: {creds_path}")
        cred = credentials.Certificate(creds_path)
    else:
        sys.exit(
            "Provide either FIREBASE_CREDENTIALS_JSON (JSON content)\n"
            "or FIREBASE_CREDENTIALS (path to service-account JSON file).\n"
            "Get one at: https://console.firebase.google.com/project/{}/settings/serviceaccounts/adminsdk".format(project_id)
        )

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {"projectId": project_id})
    return firestore.client(), project_id


def read_local_store(path):
    if not path.exists():
        sys.exit(f"Local store not found at {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def already_has_data(db):
    """Return True if Firestore already has any users (sign of prior data)."""
    snapshot = list(db.collection("users").limit(1).stream())
    return bool(snapshot)


def write_collections(db, data):
    """Write each collection's documents using their natural id field."""
    written = {}
    for name in COLLECTIONS:
        items = data.get(name, []) or []
        count = 0
        batch = db.batch()
        for index, item in enumerate(items):
            doc_id = item.get("id") or item.get("uid")
            if not doc_id:
                # Use a stable derived id if the item lacks one (e.g. some auditLogs)
                doc_id = f"{name}_{index}"
            ref = db.collection(name).document(doc_id)
            batch.set(ref, item)
            count += 1
            if count % 400 == 0:
                batch.commit()
                batch = db.batch()
        batch.commit()
        written[name] = count

    # userPermissions is a dict keyed by uid (not a list)
    perms = data.get("userPermissions", {}) or {}
    perm_count = 0
    batch = db.batch()
    for uid, perm_doc in perms.items():
        batch.set(db.collection("userPermissions").document(uid), perm_doc)
        perm_count += 1
        if perm_count % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    written["userPermissions"] = perm_count

    # ticketCounters → store the "default" counter
    counter = (data.get("ticketCounters") or {}).get("default")
    if counter:
        db.collection("ticketCounters").document("default").set(counter)
        written["ticketCounters"] = 1
    else:
        written["ticketCounters"] = 0

    return written


def main():
    parser = argparse.ArgumentParser(description="Upload local JSON store to Firestore.")
    parser.add_argument("--source", default=str(ROOT / "data" / "phase1_store.json"),
                        help="Path to the local JSON store.")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite even if Firestore already has data.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be uploaded but don't write.")
    args = parser.parse_args()

    source = Path(args.source)
    print(f"Reading local store: {source}")
    data = read_local_store(source)
    counts = {k: (len(v) if isinstance(v, list) else (len(v) if isinstance(v, dict) else 1)) for k, v in data.items()}
    print("Source counts:", counts)

    if args.dry_run:
        print("Dry run: skipping Firestore connection and writes.")
        return

    db, project_id = init_firestore()
    print(f"Connected to Firestore project: {project_id}")

    if already_has_data(db) and not args.force:
        print("Firestore already has data (users collection is non-empty).")
        print("Re-run with --force to overwrite.")
        sys.exit(1)

    written = write_collections(db, data)
    print("Upload complete:")
    for name, count in written.items():
        print(f"  {name}: {count}")
    print(f"\nDone. Open https://console.firebase.google.com/project/{project_id}/firestore")


if __name__ == "__main__":
    main()
