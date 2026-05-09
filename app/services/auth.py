from functools import wraps

from flask import current_app, flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash

from app.services.firebase_auth import firebase_enabled, firebase_sign_in


def login_user(repo, email, password):
    firebase_session = None
    if firebase_enabled():
        firebase_session, error = firebase_sign_in(email, password)
        if error:
            return None, error
        user = repo.get_user(firebase_session.get("localId")) or repo.get_user_by_email(email)
    else:
        user = repo.get_user_by_email(email)

    if not user:
        return None, "User is authenticated but not registered in the application."
    if user.get("isDeleted"):
        return None, "This user has been deleted."
    if not user.get("isActive"):
        return None, "This user is inactive."
    if not firebase_session and not check_password_hash(user.get("passwordHash", ""), password):
        return None, "Invalid email or password."

    session.clear()
    session["uid"] = user["uid"]
    if firebase_session:
        session["firebase_id_token"] = firebase_session.get("idToken")
    return user, ""


def logout_user():
    session.clear()


def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    return current_app.repo.get_user(uid)


def current_permissions():
    user = current_user()
    if not user:
        return {}
    return current_app.repo.get_permissions(user["uid"])


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def permission_required(permission):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                return redirect(url_for("auth.login", next=request.path))
            permissions = current_permissions()
            if not permissions.get(permission):
                return redirect(url_for("errors.unauthorized"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def prevent_self_destructive_action(target_uid):
    user = current_user()
    if user and user["uid"] == target_uid:
        flash("You cannot perform this action on your own active session.", "error")
        return True
    return False
