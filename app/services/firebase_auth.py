import json
import urllib.error
import urllib.request

from flask import current_app


def firebase_enabled():
    return current_app.config.get("AUTH_PROVIDER") == "firebase"


# When Firebase Auth gives one of these errors, the user might still be valid
# locally (e.g. they were seeded into the local repo but never provisioned in
# Firebase Auth yet). The login flow falls back to a local password check.
RECOVERABLE_FIREBASE_ERRORS = {
    "EMAIL_NOT_FOUND",
    "USER_NOT_FOUND",
    "INVALID_LOGIN_CREDENTIALS",  # current Firebase code for "no such user / wrong password"
    "OPERATION_NOT_ALLOWED",
    "CONFIGURATION_NOT_FOUND",
    "MISSING_PASSWORD",
    "MISSING_EMAIL",
    "API_KEY_INVALID",
    "NETWORK",  # synthetic — connection / DNS / timeout
}


def firebase_sign_in(email, password):
    api_key = current_app.config.get("FIREBASE_API_KEY")
    if not api_key:
        return None, {"code": "API_KEY_INVALID", "message": "Firebase API key is missing."}

    payload = json.dumps(
        {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            return json.loads(response.read().decode("utf-8")), None
    except urllib.error.HTTPError as error:
        try:
            body = json.loads(error.read().decode("utf-8"))
            firebase_error = body.get("error", {})
            message = firebase_error.get("message", "Firebase login failed.")
            code = (message.split(":", 1)[0] or "").strip().upper().replace(" ", "_")
        except json.JSONDecodeError:
            message = "Firebase login failed."
            code = "UNKNOWN"
        return None, {"code": code, "message": message}
    except urllib.error.URLError:
        return None, {"code": "NETWORK", "message": "Firebase login service is not reachable."}


def provision_firebase_user(user, password):
    credentials = current_app.config.get("FIREBASE_CREDENTIALS")
    if not credentials:
        return "Firebase credentials are missing; user created locally only."

    try:
        import firebase_admin
        from firebase_admin import auth, credentials as firebase_credentials
    except ImportError:
        return "firebase-admin is not installed; user created locally only."

    try:
        if not firebase_admin._apps:
            cred = firebase_credentials.Certificate(credentials)
            firebase_admin.initialize_app(cred)

        try:
            auth.create_user(
                uid=user["uid"],
                email=user["email"],
                password=password,
                display_name=user["fullName"],
                disabled=not user.get("isActive", True),
            )
        except auth.EmailAlreadyExistsError:
            auth.update_user(
                user["uid"],
                email=user["email"],
                password=password,
                display_name=user["fullName"],
                disabled=not user.get("isActive", True),
            )
        return ""
    except Exception as error:
        return f"Firebase user provisioning failed: {error}"
