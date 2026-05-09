"""Prepare a Firebase service-account JSON for pasting into Vercel env vars.

Vercel env-var inputs accept multi-line text just fine — but you can only paste
one value at a time. This script reads a serviceAccount.json file, validates
that it looks like a Firebase service-account, and prints the value to copy.

Usage:
    python scripts/prepare_vercel_env.py
    python scripts/prepare_vercel_env.py --file serviceAccount.json
    python scripts/prepare_vercel_env.py --file serviceAccount.json --one-line
"""
import argparse
import json
import sys
from pathlib import Path


REQUIRED_KEYS = {
    "type", "project_id", "private_key_id", "private_key",
    "client_email", "client_id",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", default="serviceAccount.json",
                        help="Path to the Firebase service-account JSON file (default: serviceAccount.json)")
    parser.add_argument("--one-line", action="store_true",
                        help="Print the JSON as a single line (use this if Vercel env input loses newlines)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        sys.exit(
            f"File not found: {path}\n\n"
            "Download a service-account JSON from:\n"
            "  https://console.firebase.google.com/project/<your-project>/settings/serviceaccounts/adminsdk\n"
            "Save it as serviceAccount.json in this folder, then re-run."
        )

    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"That file is not valid JSON: {e}")

    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        sys.exit(f"This does not look like a Firebase service account. Missing keys: {sorted(missing)}")

    project_id = data.get("project_id", "")
    client_email = data.get("client_email", "")

    print()
    print("=" * 72)
    print("  Vercel Environment Variables — paste each value separately")
    print("=" * 72)
    print()
    print(f"  Name:  APP_STORAGE_MODE")
    print(f"  Value: firebase")
    print()
    print(f"  Name:  FIREBASE_PROJECT_ID")
    print(f"  Value: {project_id}")
    print()
    print(f"  Name:  SECRET_KEY")
    print(f"  Value: (paste any long random string, e.g. {generate_secret()})")
    print()
    print(f"  Name:  FIREBASE_CREDENTIALS_JSON")
    print(f"  Value: (the JSON content shown below)")
    print()
    print("-" * 72)
    print(f"  Service account email: {client_email}")
    print("-" * 72)
    print()

    if args.one_line:
        # Compact JSON, no whitespace.
        print(json.dumps(data, separators=(",", ":")))
    else:
        # Pretty JSON — Vercel env-var inputs preserve newlines and load it fine.
        print(json.dumps(data, indent=2))

    print()
    print("=" * 72)
    print("  After setting all 4 env vars, click 'Redeploy' on the latest")
    print("  deployment in Vercel. The app should boot in under 30 seconds.")
    print("=" * 72)


def generate_secret(length=48):
    import secrets, string
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


if __name__ == "__main__":
    main()
