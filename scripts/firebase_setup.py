"""One-shot Firebase setup: upload local data to Firestore AND provision
the seeded users in Firebase Authentication.

Run this once after creating your Firebase project and downloading a
service-account JSON. After this completes:

  - Firestore has every collection populated from data/phase1_store.json
    (users, tickets, notes, history, notifications, audit logs, etc.)
  - Firebase Authentication has accounts for every seeded user with
    their known seed passwords, so the Flask app can log them in via
    AUTH_PROVIDER=firebase

Usage:
    # Drop your serviceAccount.json into the project root, then:
    python scripts/firebase_setup.py

    # Or pass an explicit path:
    python scripts/firebase_setup.py --credentials path/to/service-account.json

    # Skip data upload (auth only):
    python scripts/firebase_setup.py --skip-data

    # Skip auth provisioning (data only):
    python scripts/firebase_setup.py --skip-auth

    # Force overwrite even if Firestore already has data:
    python scripts/firebase_setup.py --force
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
    pass

import firebase_admin
from firebase_admin import auth, credentials, firestore


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

# Known seed passwords. Used only to provision the demo users into Firebase Auth.
# Once they exist there, change passwords from the Firebase console or admin UI.
SEED_PASSWORDS = {
    "admin@company.com":     "Admin@123",
    "requester@company.com": "Request@123",
    "approver@company.com":  "Approve@123",
    "teamlead@company.com":  "Teamlead@123",
    "member@company.com":    "Member@123",
}


def resolve_credentials(args):
    """Find a usable service-account, returning a credentials.Certificate."""
    # 1. Explicit --credentials wins.
    if args.credentials:
        path = Path(args.credentials)
        if not path.exists():
            sys.exit(f"--credentials path not found: {path}")
        return credentials.Certificate(str(path)), f"file: {path}"

    # 2. FIREBASE_CREDENTIALS_JSON (env var with JSON content) — works on Vercel/Render.
    creds_json = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()
    if creds_json:
        try:
            return credentials.Certificate(json.loads(creds_json)), "env: FIREBASE_CREDENTIALS_JSON"
        except json.JSONDecodeError as e:
            sys.exit(f"FIREBASE_CREDENTIALS_JSON env var is not valid JSON: {e}")

    # 3. FIREBASE_CREDENTIALS (env var with file path).
    creds_path = os.environ.get("FIREBASE_CREDENTIALS", "").strip()
    if creds_path:
        path = Path(creds_path)
        if not path.exists():
            sys.exit(f"FIREBASE_CREDENTIALS env var points to a missing file: {path}")
        return credentials.Certificate(str(path)), f"env: FIREBASE_CREDENTIALS -> {path}"

    # 4. Convention: ./serviceAccount.json
    default = ROOT / "serviceAccount.json"
    if default.exists():
        return credentials.Certificate(str(default)), f"default: {default}"

    # Nothing found.
    project = os.environ.get("FIREBASE_PROJECT_ID", "<your-project>")
    sys.exit(
        "\nNo Firebase service-account credentials found.\n\n"
        "How to get one:\n"
        f"  1. Open https://console.firebase.google.com/project/{project}/settings/serviceaccounts/adminsdk\n"
        "  2. Click 'Generate new private key' (downloads a JSON file)\n"
        "  3. Save it as 'serviceAccount.json' in this folder (E:\\TICKET)\n"
        "  4. Re-run: python scripts\\firebase_setup.py\n\n"
        "Alternatives: pass --credentials <path>, or set FIREBASE_CREDENTIALS_JSON env var.\n"
    )


def init_firebase(args):
    cred, source = resolve_credentials(args)
    project_id = os.environ.get("FIREBASE_PROJECT_ID", "").strip() or None
    if not firebase_admin._apps:
        if project_id:
            firebase_admin.initialize_app(cred, {"projectId": project_id})
        else:
            firebase_admin.initialize_app(cred)
    db = firestore.client()
    print(f"  credentials  : {source}")
    print(f"  project      : {project_id or db.project}")
    return db, project_id or db.project


def upload_collections(db, data, force):
    """Push every collection from local JSON to Firestore."""
    if not force and any(db.collection("users").limit(1).stream()):
        print("\nFirestore already has data in 'users'. Skipping data upload.")
        print("Re-run with --force to overwrite.")
        return None

    print("\nUploading collections...")
    written = {}
    for name in COLLECTIONS:
        items = data.get(name, []) or []
        batch = db.batch()
        count = 0
        for index, item in enumerate(items):
            doc_id = item.get("id") or item.get("uid") or f"{name}_{index}"
            batch.set(db.collection(name).document(doc_id), item)
            count += 1
            if count % 400 == 0:
                batch.commit()
                batch = db.batch()
        batch.commit()
        written[name] = count
        print(f"  {name:25s} {count:5d} docs")

    perms = data.get("userPermissions", {}) or {}
    batch = db.batch()
    pcount = 0
    for uid, perm_doc in perms.items():
        batch.set(db.collection("userPermissions").document(uid), perm_doc)
        pcount += 1
        if pcount % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    written["userPermissions"] = pcount
    print(f"  {'userPermissions':25s} {pcount:5d} docs")

    counter = (data.get("ticketCounters") or {}).get("default")
    if counter:
        db.collection("ticketCounters").document("default").set(counter)
        written["ticketCounters"] = 1
        print(f"  {'ticketCounters':25s}     1 doc")

    return written


def provision_auth_users(data):
    """Create / update Firebase Authentication accounts for seeded users."""
    print("\nProvisioning Firebase Authentication users...")
    created = 0
    updated = 0
    skipped = 0

    for user in data.get("users", []) or []:
        if user.get("isDeleted"):
            continue
        email = (user.get("email") or "").strip().lower()
        if not email:
            continue
        password = SEED_PASSWORDS.get(email)
        if not password:
            print(f"  SKIP  {email:30s}  (no known seed password — set one in the Firebase console)")
            skipped += 1
            continue

        kwargs = dict(
            uid=user["uid"],
            email=email,
            password=password,
            display_name=user.get("fullName") or email,
            disabled=not user.get("isActive", True),
        )
        try:
            try:
                auth.create_user(**kwargs)
                print(f"  NEW   {email:30s}  password={password}")
                created += 1
            except auth.UidAlreadyExistsError:
                # Same UID already exists — update password and metadata.
                auth.update_user(user["uid"],
                                 email=email,
                                 password=password,
                                 display_name=kwargs["display_name"],
                                 disabled=kwargs["disabled"])
                print(f"  UPD   {email:30s}  (uid match) password={password}")
                updated += 1
            except auth.EmailAlreadyExistsError:
                # Same email registered under a different uid — update by email lookup.
                existing = auth.get_user_by_email(email)
                auth.update_user(existing.uid,
                                 password=password,
                                 display_name=kwargs["display_name"],
                                 disabled=kwargs["disabled"])
                print(f"  UPD   {email:30s}  (email match) password={password}")
                updated += 1
        except Exception as error:
            print(f"  FAIL  {email:30s}  {error}")

    print(f"\n  created={created}  updated={updated}  skipped={skipped}")
    return created + updated


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--credentials", help="Path to a Firebase service-account JSON file.")
    parser.add_argument("--source", default=str(ROOT / "data" / "phase1_store.json"),
                        help="Path to the local JSON store (default: data/phase1_store.json).")
    parser.add_argument("--skip-data", action="store_true", help="Don't upload Firestore data.")
    parser.add_argument("--skip-auth", action="store_true", help="Don't provision Firebase Auth users.")
    parser.add_argument("--force", action="store_true", help="Overwrite Firestore data even if it's already populated.")
    args = parser.parse_args()

    print("=" * 64)
    print("  KG Ticket Control — Firebase setup")
    print("=" * 64)

    db, project = init_firebase(args)

    source = Path(args.source)
    if not source.exists():
        sys.exit(f"\nSource JSON not found: {source}")
    print(f"  source       : {source}")
    data = json.loads(source.read_text(encoding="utf-8"))
    print(f"  loaded       : {len(data.get('users', []))} users, {len(data.get('tickets', []))} tickets, "
          f"{len(data.get('notifications', []))} notifications")

    if not args.skip_data:
        upload_collections(db, data, args.force)
    else:
        print("\nSkipping data upload (--skip-data).")

    if not args.skip_auth:
        provision_auth_users(data)
    else:
        print("\nSkipping auth provisioning (--skip-auth).")

    print("\n" + "=" * 64)
    print("  Done.")
    print("=" * 64)
    print(f"\n  Firestore : https://console.firebase.google.com/project/{project}/firestore")
    print(f"  Auth users: https://console.firebase.google.com/project/{project}/authentication/users")
    print()
    print("  Next steps:")
    print("  1. Set AUTH_PROVIDER=firebase in your .env (and on Vercel)")
    print("  2. Restart Flask: python run.py")
    print("  3. Log in with admin@company.com / Admin@123 — now backed by Firebase Auth.")


if __name__ == "__main__":
    main()
