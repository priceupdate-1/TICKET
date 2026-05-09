from flask import Flask

from app.config import Config
from app.services.auth import current_permissions, current_user
from app.services.firebase_repository import FirestoreRepository
from app.services.repository import JsonRepository


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
    app = Flask(__name__)
    app.config.from_object(config_class)
    if app.config["STORAGE_MODE"] == "firebase":
        try:
            app.repo = FirestoreRepository(
                app.config["FIREBASE_CREDENTIALS"],
                app.config.get("FIREBASE_PROJECT_ID"),
                credentials_json=app.config.get("FIREBASE_CREDENTIALS_JSON"),
            )
        except RuntimeError as error:
            app.logger.warning("Falling back to local JSON storage: %s", error)
            app.repo = JsonRepository(app.config["LOCAL_STORE_PATH"])
    else:
        app.repo = JsonRepository(app.config["LOCAL_STORE_PATH"])

    from app.routes import auth_bp, dashboard_bp, errors_bp, profile_bp, settings_bp, tickets_bp, users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(errors_bp)

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
        user = current_user()
        permissions = current_permissions()
        systems = []
        if user:
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
