from flask import Flask, render_template_string

from app.config import Config
from app.services.auth import current_permissions, current_user
from app.services.firebase_repository import FirestoreRepository
from app.services.repository import JsonRepository


_SETUP_HELP_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Setup needed · KG Ticket Control</title>
    <style>
      body { font-family: -apple-system, Segoe UI, Inter, sans-serif; background: #f6f7f9; color: #0f172a; margin: 0; padding: 40px 20px; line-height: 1.55; }
      .card { max-width: 720px; margin: 0 auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 32px 36px; box-shadow: 0 12px 28px rgba(15,23,42,0.08); }
      h1 { font-size: 22px; margin: 0 0 6px; }
      p.sub { color: #64748b; margin: 0 0 20px; font-size: 14px; }
      h2 { font-size: 14px; margin: 20px 0 8px; color: #2563eb; text-transform: uppercase; letter-spacing: 0.05em; }
      ol { padding-left: 22px; }
      li { margin-bottom: 8px; font-size: 14px; }
      code, pre { background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px; padding: 2px 8px; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12.5px; }
      pre { padding: 12px 14px; overflow-x: auto; white-space: pre-wrap; }
      .err { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; border-radius: 8px; padding: 10px 14px; font-size: 13px; margin: 0 0 18px; }
      a { color: #2563eb; }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>One step left to finish setup</h1>
      <p class="sub">The app is running but it can't reach a database yet.</p>
      <div class="err">Reason: {{ error }}</div>

      <h2>Set these env vars on Vercel</h2>
      <p>Project Settings &rarr; Environment Variables (Production), then redeploy:</p>
      <pre>APP_STORAGE_MODE        = firebase
FIREBASE_PROJECT_ID     = {{ project }}
FIREBASE_CREDENTIALS_JSON = (paste the entire serviceAccount.json content as ONE line)
SECRET_KEY              = (any long random string)</pre>

      <h2>Where to get FIREBASE_CREDENTIALS_JSON</h2>
      <ol>
        <li>Open <a href="https://console.firebase.google.com/project/{{ project }}/settings/serviceaccounts/adminsdk" target="_blank" rel="noopener">Firebase Console &rarr; Service Accounts</a></li>
        <li>Click <strong>Generate new private key</strong> &rarr; downloads a JSON file</li>
        <li>Open it in a text editor, copy the entire contents</li>
        <li>In Vercel, paste it as the value of <code>FIREBASE_CREDENTIALS_JSON</code> (Vercel preserves newlines in env vars, so multi-line JSON is fine)</li>
        <li>Click <strong>Redeploy</strong> on the latest deployment</li>
      </ol>

      <h2>Tip</h2>
      <p>Run <code>python scripts/prepare_vercel_env.py</code> locally to print the JSON pre-formatted for paste-into-Vercel.</p>
    </div>
  </body>
</html>"""


# Backend status -> user-friendly label (Phase 3 simplification)
FRIENDLY_STATUS = {
    "Draft": "Draft",
    "Submitted": "Submitted",
    "Pending Authorization": "Waiting for Approval",
    "Need More Information": "Need Your Reply",
    "Approved": "Approved",
    "Assigned to Team": "Assigned to Team",
    "Assigned To Team": "Assigned to Team",
    "In Progress": "Work in Progress",
    "Work Updated": "Work Updated",
    "On Hold": "On Hold",
    "Completed": "Work Done",
    "Verified": "Checked",
    "Closed": "Closed",
    "Reopened": "Reopened",
    "Rejected": "Rejected",
    "Cancelled": "Cancelled",
}

STATUS_CSS = {
    "Draft":                    "is-draft",
    "Submitted":                "is-submitted",
    "Pending Authorization":    "is-pending",
    "Need More Information":    "is-info-needed",
    "Approved":                 "is-approved",
    "Assigned to Team":         "is-assigned",
    "Assigned To Team":         "is-assigned",
    "In Progress":              "is-progress",
    "Work Updated":             "is-progress",
    "On Hold":                  "is-hold",
    "Completed":                "is-completed",
    "Verified":                 "is-verified",
    "Closed":                   "is-closed",
    "Reopened":                 "is-reopened",
    "Rejected":                 "is-rejected",
    "Cancelled":                "is-cancelled",
}


def create_app(config_class=Config):
    import os
    app = Flask(__name__)
    app.config.from_object(config_class)

    on_vercel = bool(os.environ.get("VERCEL"))
    storage_error = None

    if app.config["STORAGE_MODE"] == "firebase":
        try:
            app.repo = FirestoreRepository(
                app.config["FIREBASE_CREDENTIALS"],
                app.config.get("FIREBASE_PROJECT_ID"),
                credentials_json=app.config.get("FIREBASE_CREDENTIALS_JSON"),
            )
        except RuntimeError as error:
            app.logger.warning("Firestore init failed: %s", error)
            storage_error = str(error)
            app.repo = None
            if not on_vercel:
                # Local dev: fall back to JSON file so user can keep working.
                try:
                    app.repo = JsonRepository(app.config["LOCAL_STORE_PATH"])
                    app.logger.warning("Falling back to local JSON storage.")
                except OSError as fs_error:
                    app.logger.error("Could not initialise local storage: %s", fs_error)
    else:
        try:
            app.repo = JsonRepository(app.config["LOCAL_STORE_PATH"])
        except OSError as fs_error:
            app.logger.error("Could not initialise local storage: %s", fs_error)
            app.repo = None
            storage_error = str(fs_error)

    app.config["STORAGE_ERROR"] = storage_error
    app.config["ON_VERCEL"] = on_vercel

    # If storage failed on production, every request shows a clear setup page
    # rather than a 500 stack trace.
    @app.before_request
    def _check_storage():
        from flask import request as flask_request, render_template_string
        if app.repo is None:
            if flask_request.path.startswith("/static/"):
                return None
            return render_template_string(
                _SETUP_HELP_TEMPLATE,
                error=storage_error or "Storage backend not configured.",
                project=app.config.get("FIREBASE_PROJECT_ID") or "<your-project-id>",
            ), 500
        return None

    from app.routes import auth_bp, dashboard_bp, errors_bp, notifications_bp, profile_bp, settings_bp, tickets_bp, users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(notifications_bp)

    @app.template_filter("friendly_status")
    def friendly_status(value):
        return FRIENDLY_STATUS.get(value, value or "")

    @app.template_filter("status_css")
    def status_css(value):
        return STATUS_CSS.get(value, "")

    @app.template_filter("ago")
    def ago(value):
        from datetime import datetime, timezone
        if not value:
            return "—"
        try:
            iso = value.replace("Z", "+00:00") if isinstance(value, str) else value
            dt = datetime.fromisoformat(iso) if isinstance(value, str) else value
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - dt
            secs = int(delta.total_seconds())
            if secs < 60:    return "just now"
            if secs < 3600:  return f"{secs // 60}m ago"
            if secs < 86400: return f"{secs // 3600}h ago"
            if secs < 604800: return f"{secs // 86400}d ago"
            return dt.strftime("%d %b %Y")
        except Exception:
            return str(value)[:19].replace("T", " ")

    @app.template_filter("initials")
    def initials(name):
        if not name:
            return "?"
        parts = [p for p in str(name).split() if p]
        return ("".join(p[0] for p in parts[:2]) or "?").upper()

    @app.context_processor
    def inject_user_context():
        user = current_user() if app.repo else None
        permissions = current_permissions() if app.repo else {}
        systems = []
        if user and app.repo:
            try:
                visible = app.repo.visible_tickets(user, permissions)
                open_statuses = {
                    "Pending Authorization", "Approved", "Assigned to Team",
                    "Assigned To Team", "In Progress", "Work Updated",
                    "On Hold", "Reopened", "Need More Information",
                }
                for system in app.repo.systems():
                    open_count = sum(
                        1 for t in visible
                        if t.get("systemId") == system["id"] and t.get("status") in open_statuses
                    )
                    total_count = sum(1 for t in visible if t.get("systemId") == system["id"])
                    systems.append({
                        "id": system["id"],
                        "name": system["name"],
                        "open_count": open_count,
                        "total_count": total_count,
                    })
            except Exception:
                systems = []
        return {
            "current_user": user,
            "current_permissions": permissions,
            "app_name": app.config["APP_NAME"],
            "nav_systems": systems,
        }

    return app
