# KG Ticket Control

Flask-based ticket management for **Lattice** and **Trybe** workflows. Phase 1 (auth, users, permissions) + Phase 2 (full ticket lifecycle) + Phase 3 (UX simplification, friendly status labels, role-based dashboard) are live. The frontend is server-rendered Jinja with a clean light theme. Data persists to **Firestore** in production, JSON locally for dev.

---

## Quick start (local)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# copy env template, then either keep APP_STORAGE_MODE=local OR
# fill FIREBASE_CREDENTIALS_JSON for Firestore
copy .env.example .env

python run.py
```

Open http://127.0.0.1:5000

**Seed admin login:** `admin@company.com` / `Admin@123`

Other seeded users:
```
requester@company.com / Request@123
approver@company.com  / Approve@123
teamlead@company.com  / Teamlead@123
member@company.com    / Member@123
```

---

## Use Firestore for data

The app already supports Firestore via the Firebase Admin SDK. Configure it in `.env`:

```ini
APP_STORAGE_MODE=firebase
FIREBASE_PROJECT_ID=kg-ticket
FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"kg-ticket", ... }
```

**Get the service-account JSON:**
1. Go to https://console.firebase.google.com/project/kg-ticket/settings/serviceaccounts/adminsdk
2. Click **Generate new private key** → it downloads a JSON file
3. Either:
   - Save it as `serviceAccount.json` in the project root and set `FIREBASE_CREDENTIALS=./serviceAccount.json`, OR
   - Paste the entire JSON content (one line) into `FIREBASE_CREDENTIALS_JSON=` in `.env`

The app auto-seeds Firestore collections on first run if they're empty.

---

## Deploy to Vercel

The repo is Vercel-ready ([vercel.json](vercel.json) + [api/index.py](api/index.py)).

1. Push this repo to GitHub.
2. Go to https://vercel.com/new → import the repo.
3. Framework preset: **Other** (Vercel auto-detects Python).
4. **Environment Variables** (Settings → Environment Variables):
   - `APP_STORAGE_MODE` = `firebase`
   - `FIREBASE_PROJECT_ID` = `kg-ticket`
   - `FIREBASE_CREDENTIALS_JSON` = *(paste full service-account JSON content as one line)*
   - `SECRET_KEY` = *(any long random string)*
5. Deploy.

> **Note:** Vercel's filesystem is ephemeral — the JSON-content env var (`FIREBASE_CREDENTIALS_JSON`) is the right approach there. Don't use the file-path option on Vercel.

### Alternative: Render / Railway
A `Procfile` is included for buildpack-style platforms:

```
web: gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

Set the same env vars listed above.

---

## What's implemented

**Phase 1 — Foundation**
- Login / logout, protected routes, permission guards
- Users CRUD: list, add, edit, view, activate, deactivate, soft delete, reset password
- Permission flags per user (assignment grid)
- Audit log of user/permission changes
- Profile + settings pages

**Phase 2 — Ticket lifecycle**
- Create / draft / submit / edit
- Queues: My Tickets, All Tickets, Pending Authorization, Team Queue, Completed
- Detail view with notes, attachments, status history
- Actions: approve, reject, send back, assign team, assign member, start work, add note, complete, close, reopen, cancel

**Phase 3 — UX simplification (this update)**
- Friendly status labels (`Pending Authorization` → `Waiting for Approval`, etc.) via Jinja filter
- Role-based dashboard: Request User, Authorized Person, Team, Admin each see relevant stat cards
- "Waiting for Your Approval" inline panel for approvers / admin
- Clean industry-level light UI with sidebar navigation, status pills, empty states, confirmation prompts on destructive actions
- Notification bell + dropdown shell in topbar (events to be wired in Phase 4)

---

## Project structure

```
app/
  __init__.py            Flask factory, Jinja filters (friendly_status, status_css, ago, initials)
  config.py              env-driven config (FIREBASE_CREDENTIALS_JSON support)
  constants.py           Permissions, statuses, system access
  routes.py              All HTTP routes
  services/
    auth.py              Login / permission decorators
    repository.py        JSON repository (default)
    firebase_repository.py  Firestore repository
    seed.py              Seed data + factories
    forms.py             Form validation helpers
    firebase_auth.py     Optional Firebase Auth provider
  static/app.css         Industry-level light UI
  templates/             Jinja templates
api/index.py             Vercel entrypoint
run.py                   Local dev entrypoint (`python run.py`)
Procfile                 Render / Railway entrypoint
vercel.json              Vercel build + routing
.env.example             Env template
trash/                   Old static prototype (kept for reference)
```

---

## Phase 4 — next up

- Wire real notifications collection + bell badge count
- Gmail SMTP for email notifications on key events
- Excel export of ticket queues
- Per-user notification preferences

These are deferred per [phase3.md](phase3.md) — UI notification flow stabilizes first, then mail uses the same events.
