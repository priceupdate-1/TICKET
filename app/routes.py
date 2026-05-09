from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for

from app.constants import (
    DEFAULT_DASHBOARDS,
    NOTE_TYPES,
    NOTE_VISIBILITIES,
    PERMISSIONS,
    SYSTEM_ACCESS,
    TICKET_PRIORITIES,
    TICKET_STATUSES,
)
from app.services.auth import (
    current_permissions,
    current_user,
    login_required,
    login_user,
    logout_user,
    permission_required,
    prevent_self_destructive_action,
)
from app.services.forms import (
    permissions_from_form,
    ticket_payload_from_form,
    user_payload_from_form,
    validate_ticket_payload,
    validate_user_payload,
)
from app.services.firebase_auth import firebase_enabled, provision_firebase_user


auth_bp = Blueprint("auth", __name__)
dashboard_bp = Blueprint("dashboard", __name__)
users_bp = Blueprint("users", __name__, url_prefix="/users")
tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")
profile_bp = Blueprint("profile", __name__)
settings_bp = Blueprint("settings", __name__)
errors_bp = Blueprint("errors", __name__)
notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notifications_bp.route("", methods=["GET"])
@login_required
def list_notifications():
    user = current_user()
    items = current_app.repo.notifications_for_user(user["uid"], limit=20)
    unread = current_app.repo.unread_notification_count(user["uid"])
    return jsonify({
        "unread": unread,
        "items": [{
            "id": n.get("id"),
            "title": n.get("title"),
            "message": n.get("message"),
            "ticketId": n.get("ticketId"),
            "ticketNo": n.get("ticketNo"),
            "type": n.get("type"),
            "isRead": bool(n.get("isRead")),
            "createdAt": n.get("createdAt"),
            "url": url_for("tickets.view_ticket", ticket_id=n["ticketId"]) if n.get("ticketId") else "",
        } for n in items],
    })


@notifications_bp.route("/<notif_id>/read", methods=["POST"])
@login_required
def mark_read(notif_id):
    user = current_user()
    ok = current_app.repo.mark_notification_read(notif_id, user["uid"])
    return jsonify({"ok": ok, "unread": current_app.repo.unread_notification_count(user["uid"])})


@notifications_bp.route("/read-all", methods=["POST"])
@login_required
def mark_all_read():
    user = current_user()
    changed = current_app.repo.mark_all_notifications_read(user["uid"])
    return jsonify({"ok": True, "changed": changed, "unread": 0})


def form_context(user=None, permissions=None):
    return {
        "user": user,
        "permissions": permissions or {},
        "user_types": current_app.repo.user_types(),
        "roles": current_app.repo.roles(),
        "departments": current_app.repo.departments(),
        "managers": current_app.repo.active_users(),
        "permission_options": PERMISSIONS,
        "system_access_options": SYSTEM_ACCESS,
        "dashboard_options": DEFAULT_DASHBOARDS,
    }


def ticket_form_context(ticket=None):
    return {
        "ticket": ticket,
        "systems": current_app.repo.systems(),
        "categories": current_app.repo.categories(),
        "areas": current_app.repo.areas(),
        "priorities": TICKET_PRIORITIES,
    }


def ticket_detail_context(ticket):
    permissions = current_permissions()
    include_internal = permissions.get("canViewAllTickets") or permissions.get("canWorkOnTicket") or permissions.get("canManageUsers")
    return {
        "ticket": ticket,
        "notes": current_app.repo.ticket_notes(ticket["id"], include_internal=include_internal),
        "history": current_app.repo.ticket_status_history(ticket["id"]),
        "attachments": current_app.repo.ticket_attachments(ticket["id"]),
        "teams": current_app.repo.teams(ticket.get("systemId")),
        "members": current_app.repo.active_users(),
        "note_types": NOTE_TYPES,
        "note_visibilities": NOTE_VISIBILITIES if include_internal else ["Public"],
        "permissions": permissions,
        "can_edit": ticket["status"] in ["Draft", "Need More Information"] and ticket["createdBy"] == current_user()["uid"],
        "can_approve": permissions.get("canApproveTicket") and ticket["status"] == "Pending Authorization",
        "can_reject": permissions.get("canRejectTicket") and ticket["status"] == "Pending Authorization",
        "can_more_info": permissions.get("canApproveTicket") and ticket["status"] == "Pending Authorization",
        "can_assign_member": permissions.get("canAssignTeam") and ticket["status"] in ["Approved", "Reopened"],
        "can_start_work": permissions.get("canWorkOnTicket") and ticket["status"] == "Assigned To Team",
        "can_complete": permissions.get("canWorkOnTicket") and ticket["status"] in ["In Progress", "On Hold"],
        "can_close": permissions.get("canCloseTicket") and ticket["status"] == "Completed",
        "can_reopen": permissions.get("canReopenTicket") and ticket["status"] in ["Closed", "Completed", "Rejected"],
        "can_cancel": ticket["createdBy"] == current_user()["uid"] and ticket["status"] in ["Draft", "Pending Authorization"],
    }


def visible_ticket_or_redirect(ticket_id):
    ticket = current_app.repo.get_ticket(ticket_id)
    if not ticket:
        flash("Ticket not found.", "error")
        return None
    visible_ids = {item["id"] for item in current_app.repo.visible_tickets(current_user(), current_permissions())}
    if ticket_id not in visible_ids:
        flash("You do not have access to this ticket.", "error")
        return None
    return ticket


@auth_bp.route("/")
def index():
    if current_user():
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("auth/login.html", email=email)
        if "@" not in email:
            flash("Enter a valid email address.", "error")
            return render_template("auth/login.html", email=email)

        user, error = login_user(current_app.repo, email, password)
        if error:
            flash(error, "error")
            return render_template("auth/login.html", email=email)

        next_url = request.args.get("next") or url_for("dashboard.dashboard")
        return redirect(next_url)

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    permissions = current_permissions()
    visible = current_app.repo.visible_tickets(user, permissions)

    def has(*statuses):
        s = set(statuses)
        return [t for t in visible if t.get("status") in s]

    own = [t for t in visible if t.get("createdBy") == user.get("uid")]
    is_admin = bool(permissions.get("canManageUsers"))
    is_approver = bool(permissions.get("canApproveTicket"))
    is_team = bool(permissions.get("canWorkOnTicket"))

    # Build role-aware stat cards (Phase 3 simplification)
    if is_admin:
        cards = [
            {"label": "Total Tickets",     "value": len(visible),                                                                     "cls": "is-info",    "foot": "All systems"},
            {"label": "Waiting Approval",  "value": len(has("Pending Authorization")),                                                "cls": "is-warning", "foot": "Need decision"},
            {"label": "In Progress",       "value": len(has("Approved", "Assigned to Team", "Assigned To Team", "In Progress", "Work Updated")), "cls": "is-brand", "foot": "Active work"},
            {"label": "Closed",            "value": len(has("Closed", "Verified")),                                                   "cls": "is-success", "foot": "Resolved"},
        ]
        subtitle = "Admin console — direct controls across all tickets."
    elif is_approver:
        my_pending = [t for t in has("Pending Authorization") if t.get("authorizedPersonId") == user.get("uid")]
        my_completed = [t for t in has("Completed") if t.get("authorizedPersonId") == user.get("uid")]
        urgent = [t for t in visible if t.get("priority") == "Urgent"]
        cards = [
            {"label": "Waiting Approval",   "value": len(my_pending),     "cls": "is-warning", "foot": "Need your decision"},
            {"label": "Need Info Pending",  "value": len(has("Need More Information")), "cls": "is-danger",  "foot": "Sent back"},
            {"label": "Awaiting Closure",   "value": len(my_completed),   "cls": "is-brand",   "foot": "Verify & close"},
            {"label": "Urgent",             "value": len(urgent),         "cls": "is-success", "foot": "High priority"},
        ]
        subtitle = "Approval desk — review, approve, send back, or close completed work."
    elif is_team:
        assigned = [t for t in visible if t.get("assignedTo") == user.get("uid")]
        in_progress = has("In Progress", "Work Updated")
        on_hold = has("On Hold")
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).date().isoformat()
        done_today = [t for t in visible if (t.get("completedAt") or "")[:10] == today]
        cards = [
            {"label": "Assigned to Me", "value": len(assigned),    "cls": "is-brand",   "foot": "Personal queue"},
            {"label": "In Progress",    "value": len(in_progress), "cls": "is-info",    "foot": "Active work"},
            {"label": "On Hold",        "value": len(on_hold),     "cls": "is-warning", "foot": "Paused"},
            {"label": "Done Today",     "value": len(done_today),  "cls": "is-success", "foot": "Completed"},
        ]
        subtitle = "Work queue — start, update, and mark items done."
    else:
        cards = [
            {"label": "My Open Tickets", "value": len([t for t in own if t.get("status") in {"Pending Authorization","Approved","Assigned to Team","Assigned To Team","In Progress","Work Updated","Reopened"}]), "cls": "is-brand",   "foot": "Currently active"},
            {"label": "Need My Reply",   "value": len([t for t in own if t.get("status") == "Need More Information"]), "cls": "is-danger",  "foot": "Waiting on you"},
            {"label": "Closed",          "value": len([t for t in own if t.get("status") in {"Closed","Verified"}]),    "cls": "is-success", "foot": "Resolved"},
            {"label": "Total Created",   "value": len(own),                                                              "cls": "is-info",    "foot": "All time"},
        ]
        subtitle = "Track your tickets and reply when more information is needed."

    pending_for_me = []
    if is_approver and not is_admin:
        pending_for_me = sorted(
            [t for t in has("Pending Authorization") if t.get("authorizedPersonId") == user.get("uid")],
            key=lambda t: t.get("updatedAt", ""), reverse=True,
        )[:5]
    elif is_admin:
        pending_for_me = sorted(has("Pending Authorization"), key=lambda t: t.get("updatedAt", ""), reverse=True)[:5]

    recent_tickets = sorted(visible, key=lambda t: t.get("updatedAt", ""), reverse=True)[:8]

    # Admin-only: per-system breakdown so admin can see Lattice vs Trybe load
    system_breakdown = []
    if is_admin:
        open_set = {"Pending Authorization", "Approved", "Assigned to Team", "Assigned To Team", "In Progress", "Work Updated", "On Hold", "Reopened", "Need More Information"}
        for system in current_app.repo.systems():
            sys_tickets = [t for t in visible if t.get("systemId") == system["id"]]
            system_breakdown.append({
                "id": system["id"],
                "name": system["name"],
                "total": len(sys_tickets),
                "open": sum(1 for t in sys_tickets if t.get("status") in open_set),
                "pending": sum(1 for t in sys_tickets if t.get("status") == "Pending Authorization"),
                "in_progress": sum(1 for t in sys_tickets if t.get("status") in {"In Progress", "Work Updated"}),
                "closed": sum(1 for t in sys_tickets if t.get("status") in {"Closed", "Verified"}),
            })

    return render_template(
        "dashboard/index.html",
        cards=cards,
        greeting_subtitle=subtitle,
        pending_for_me=pending_for_me,
        recent_tickets=recent_tickets,
        system_breakdown=system_breakdown,
        is_admin_view=is_admin,
    )


@users_bp.route("/")
@login_required
@permission_required("canManageUsers")
def list_users():
    lookup = current_app.repo.all_data()
    return render_template(
        "users/list.html",
        users=current_app.repo.users(),
        user_types={item["id"]: item for item in lookup["userTypes"]},
        roles={item["id"]: item for item in lookup["roles"]},
        departments={item["id"]: item for item in lookup["departments"]},
    )


@users_bp.route("/add", methods=["GET", "POST"])
@login_required
@permission_required("canManageUsers")
def add_user():
    if request.method == "POST":
        payload = user_payload_from_form(request.form, include_password=True)
        permissions = permissions_from_form(request.form)
        errors = validate_user_payload(payload, creating=True)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("users/form.html", mode="add", **form_context(payload, permissions))
        try:
            user = current_app.repo.create_user(payload, permissions, current_user())
            if firebase_enabled():
                warning = provision_firebase_user(user, payload["password"])
                if warning:
                    flash(warning, "error")
            flash("User created successfully.", "success")
            return redirect(url_for("users.view_user", uid=user["uid"]))
        except ValueError as error:
            flash(str(error), "error")
            return render_template("users/form.html", mode="add", **form_context(payload, permissions))

    return render_template("users/form.html", mode="add", **form_context())


@users_bp.route("/edit/<uid>", methods=["GET", "POST"])
@login_required
@permission_required("canManageUsers")
def edit_user(uid):
    user = current_app.repo.get_user(uid)
    if not user or user.get("isDeleted"):
        flash("User not found.", "error")
        return redirect(url_for("users.list_users"))

    if request.method == "POST":
        payload = user_payload_from_form(request.form, include_password=True)
        payload["email"] = user["email"]
        payload["employeeCode"] = user["employeeCode"]
        permissions = permissions_from_form(request.form)
        errors = validate_user_payload(payload, creating=False)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("users/form.html", mode="edit", uid=uid, **form_context({**user, **payload}, permissions))

        current_app.repo.update_user(uid, payload, permissions, current_user())
        flash("User updated successfully.", "success")
        return redirect(url_for("users.view_user", uid=uid))

    return render_template(
        "users/form.html",
        mode="edit",
        uid=uid,
        **form_context(user, current_app.repo.get_permissions(uid)),
    )


@users_bp.route("/view/<uid>")
@login_required
@permission_required("canManageUsers")
def view_user(uid):
    user = current_app.repo.get_user(uid)
    if not user or user.get("isDeleted"):
        flash("User not found.", "error")
        return redirect(url_for("users.list_users"))
    lookup = current_app.repo.all_data()
    return render_template(
        "users/view.html",
        user=user,
        permissions=current_app.repo.get_permissions(uid),
        permission_options=PERMISSIONS,
        user_types={item["id"]: item for item in lookup["userTypes"]},
        roles={item["id"]: item for item in lookup["roles"]},
        departments={item["id"]: item for item in lookup["departments"]},
    )


@users_bp.route("/activate/<uid>", methods=["POST"])
@login_required
@permission_required("canManageUsers")
def activate_user(uid):
    current_app.repo.set_user_active(uid, True, current_user())
    flash("User activated.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/deactivate/<uid>", methods=["POST"])
@login_required
@permission_required("canManageUsers")
def deactivate_user(uid):
    if prevent_self_destructive_action(uid):
        return redirect(url_for("users.list_users"))
    current_app.repo.set_user_active(uid, False, current_user())
    flash("User deactivated.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/delete/<uid>", methods=["POST"])
@login_required
@permission_required("canManageUsers")
def delete_user(uid):
    if prevent_self_destructive_action(uid):
        return redirect(url_for("users.list_users"))
    current_app.repo.soft_delete_user(uid, current_user())
    flash("User deleted.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/reset-password/<uid>", methods=["POST"])
@login_required
@permission_required("canManageUsers")
def reset_password(uid):
    user = current_app.repo.get_user(uid)
    if not user or user.get("isDeleted"):
        flash("User not found.", "error")
        return redirect(url_for("users.list_users"))
    permissions = current_app.repo.get_permissions(uid)
    payload = {
        "fullName": user["fullName"],
        "mobileNo": user.get("mobileNo", ""),
        "departmentId": user.get("departmentId", ""),
        "designation": user.get("designation", ""),
        "reportingManagerId": user.get("reportingManagerId", ""),
        "userTypeId": user.get("userTypeId", ""),
        "roleId": user.get("roleId", ""),
        "systemAccess": user.get("systemAccess", []),
        "defaultDashboard": user.get("defaultDashboard", "requester"),
        "isActive": user.get("isActive", False),
        "notificationEmail": user.get("notificationEmail", False),
        "notificationInApp": user.get("notificationInApp", False),
        "password": "Change@123",
    }
    current_app.repo.update_user(uid, payload, permissions, current_user())
    flash("Password reset to Change@123.", "success")
    return redirect(url_for("users.view_user", uid=uid))


@tickets_bp.route("/")
@login_required
def all_tickets():
    system_id = request.args.get("system", "").strip()
    tickets = current_app.repo.visible_tickets(current_user(), current_permissions())
    heading = "All Tickets"
    description = "Tickets visible to your current role and permissions."
    if system_id:
        tickets = [t for t in tickets if t.get("systemId") == system_id]
        system_name = next((s["name"] for s in current_app.repo.systems() if s["id"] == system_id), "")
        if system_name:
            heading = f"{system_name} Tickets"
            description = f"All {system_name} tickets you can access."
    return render_template(
        "tickets/list.html",
        tickets=tickets,
        page_heading=heading,
        page_description=description,
        statuses=TICKET_STATUSES,
        active_system=system_id,
    )


@tickets_bp.route("/my")
@login_required
@permission_required("canViewOwnTicket")
def my_tickets():
    tickets = [
        ticket
        for ticket in current_app.repo.visible_tickets(current_user(), current_permissions())
        if ticket["createdBy"] == current_user()["uid"]
    ]
    return render_template(
        "tickets/list.html",
        tickets=tickets,
        page_heading="My Tickets",
        page_description="Tickets created by the logged-in user.",
        statuses=TICKET_STATUSES,
    )


@tickets_bp.route("/pending-authorization")
@login_required
@permission_required("canApproveTicket")
def pending_authorization():
    permissions = current_permissions()
    tickets = [
        ticket
        for ticket in current_app.repo.visible_tickets(current_user(), permissions)
        if ticket["status"] == "Pending Authorization"
        and (permissions.get("canViewAllTickets") or ticket.get("authorizedPersonId") == current_user()["uid"])
    ]
    return render_template(
        "tickets/list.html",
        tickets=tickets,
        page_heading="Pending Authorization",
        page_description="Tickets waiting for approval, rejection, or more information.",
        statuses=TICKET_STATUSES,
    )


@tickets_bp.route("/team")
@login_required
@permission_required("canWorkOnTicket")
def team_tickets():
    tickets = [
        ticket
        for ticket in current_app.repo.visible_tickets(current_user(), current_permissions())
        if ticket["status"] in ["Approved", "Assigned To Team", "In Progress", "On Hold"]
    ]
    return render_template(
        "tickets/list.html",
        tickets=tickets,
        page_heading="Team Tickets",
        page_description="Approved and assigned work queues for team delivery.",
        statuses=TICKET_STATUSES,
    )


@tickets_bp.route("/completed")
@login_required
def completed_tickets():
    tickets = [
        ticket
        for ticket in current_app.repo.visible_tickets(current_user(), current_permissions())
        if ticket["status"] == "Completed"
    ]
    return render_template(
        "tickets/list.html",
        tickets=tickets,
        page_heading="Completed Tickets",
        page_description="Completed tickets waiting for closure or reopen decision.",
        statuses=TICKET_STATUSES,
    )


@tickets_bp.route("/approved")
@login_required
def approved_tickets():
    tickets = [
        ticket
        for ticket in current_app.repo.visible_tickets(current_user(), current_permissions())
        if ticket["status"] == "Approved"
    ]
    return render_template(
        "tickets/list.html",
        tickets=tickets,
        page_heading="Approved Tickets",
        page_description="Approved tickets ready for team assignment.",
        statuses=TICKET_STATUSES,
    )


@tickets_bp.route("/create", methods=["GET", "POST"])
@login_required
@permission_required("canCreateTicket")
def create_ticket():
    if request.method == "POST":
        payload = ticket_payload_from_form(request.form)
        errors = validate_ticket_payload(payload)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("tickets/form.html", mode="create", **ticket_form_context(payload))
        submit = request.form.get("intent") != "draft"
        try:
            ticket = current_app.repo.create_ticket(payload, current_user(), submit=submit)
            flash("Ticket submitted." if submit else "Ticket saved as draft.", "success")
            return redirect(url_for("tickets.view_ticket", ticket_id=ticket["id"]))
        except ValueError as error:
            flash(str(error), "error")
            return render_template("tickets/form.html", mode="create", **ticket_form_context(payload))
    return render_template("tickets/form.html", mode="create", **ticket_form_context())


@tickets_bp.route("/edit/<ticket_id>", methods=["GET", "POST"])
@login_required
def edit_ticket(ticket_id):
    ticket = visible_ticket_or_redirect(ticket_id)
    if not ticket:
        return redirect(url_for("tickets.all_tickets"))
    if ticket["createdBy"] != current_user()["uid"] or ticket["status"] not in ["Draft", "Need More Information"]:
        flash("This ticket cannot be edited now.", "error")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))
    if request.method == "POST":
        payload = ticket_payload_from_form(request.form)
        errors = validate_ticket_payload(payload)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("tickets/form.html", mode="edit", **ticket_form_context({**ticket, **payload}))
        submit = request.form.get("intent") != "draft"
        current_app.repo.update_ticket(ticket_id, payload, current_user(), submit=submit)
        flash("Ticket updated.", "success")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))
    return render_template("tickets/form.html", mode="edit", **ticket_form_context(ticket))


@tickets_bp.route("/view/<ticket_id>")
@login_required
def view_ticket(ticket_id):
    ticket = visible_ticket_or_redirect(ticket_id)
    if not ticket:
        return redirect(url_for("tickets.all_tickets"))
    return render_template("tickets/view.html", **ticket_detail_context(ticket))


@tickets_bp.route("/approve/<ticket_id>", methods=["POST"])
@login_required
@permission_required("canApproveTicket")
def approve_ticket(ticket_id):
    if not visible_ticket_or_redirect(ticket_id):
        return redirect(url_for("tickets.all_tickets"))
    try:
        current_app.repo.approve_ticket(
            ticket_id,
            request.form.get("teamId", ""),
            request.form.get("dueDate", ""),
            request.form.get("note", ""),
            current_user(),
        )
        flash("Ticket approved.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@tickets_bp.route("/reject/<ticket_id>", methods=["POST"])
@login_required
@permission_required("canRejectTicket")
def reject_ticket(ticket_id):
    if not visible_ticket_or_redirect(ticket_id):
        return redirect(url_for("tickets.all_tickets"))
    reason = request.form.get("reason", "").strip()
    if not reason:
        flash("Rejection reason is required.", "error")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))
    current_app.repo.reject_ticket(ticket_id, reason, current_user())
    flash("Ticket rejected.", "success")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@tickets_bp.route("/need-more-info/<ticket_id>", methods=["POST"])
@login_required
@permission_required("canApproveTicket")
def need_more_info(ticket_id):
    if not visible_ticket_or_redirect(ticket_id):
        return redirect(url_for("tickets.all_tickets"))
    note = request.form.get("note", "").strip()
    if not note:
        flash("More information note is required.", "error")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))
    current_app.repo.request_more_info(ticket_id, note, current_user())
    flash("Ticket returned for more information.", "success")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@tickets_bp.route("/assign-member/<ticket_id>", methods=["POST"])
@login_required
@permission_required("canAssignTeam")
def assign_member(ticket_id):
    if not visible_ticket_or_redirect(ticket_id):
        return redirect(url_for("tickets.all_tickets"))
    try:
        current_app.repo.assign_member(
            ticket_id,
            request.form.get("memberId", ""),
            request.form.get("note", ""),
            current_user(),
        )
        flash("Team member assigned.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@tickets_bp.route("/start-work/<ticket_id>", methods=["POST"])
@login_required
@permission_required("canWorkOnTicket")
def start_work(ticket_id):
    if not visible_ticket_or_redirect(ticket_id):
        return redirect(url_for("tickets.all_tickets"))
    current_app.repo.start_work(ticket_id, request.form.get("note", ""), current_user())
    flash("Work started.", "success")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@tickets_bp.route("/add-note/<ticket_id>", methods=["POST"])
@login_required
@permission_required("canAddNotes")
def add_ticket_note(ticket_id):
    if not visible_ticket_or_redirect(ticket_id):
        return redirect(url_for("tickets.all_tickets"))
    note_text = request.form.get("noteText", "").strip()
    if not note_text:
        flash("Note text is required.", "error")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))
    current_app.repo.add_ticket_note(
        ticket_id,
        request.form.get("noteType", "User Comment"),
        note_text,
        request.form.get("visibility", "Public"),
        current_user(),
    )
    flash("Note added.", "success")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@tickets_bp.route("/complete/<ticket_id>", methods=["POST"])
@login_required
@permission_required("canWorkOnTicket")
def complete_ticket(ticket_id):
    if not visible_ticket_or_redirect(ticket_id):
        return redirect(url_for("tickets.all_tickets"))
    resolution = request.form.get("resolutionNote", "").strip()
    if not resolution:
        flash("Resolution note is required.", "error")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))
    current_app.repo.complete_ticket(ticket_id, resolution, current_user())
    flash("Ticket completed.", "success")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@tickets_bp.route("/close/<ticket_id>", methods=["POST"])
@login_required
@permission_required("canCloseTicket")
def close_ticket(ticket_id):
    if not visible_ticket_or_redirect(ticket_id):
        return redirect(url_for("tickets.all_tickets"))
    current_app.repo.close_ticket(ticket_id, request.form.get("closureNote", ""), current_user())
    flash("Ticket closed.", "success")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@tickets_bp.route("/reopen/<ticket_id>", methods=["POST"])
@login_required
@permission_required("canReopenTicket")
def reopen_ticket(ticket_id):
    if not visible_ticket_or_redirect(ticket_id):
        return redirect(url_for("tickets.all_tickets"))
    reason = request.form.get("reason", "").strip()
    if not reason:
        flash("Reopen reason is required.", "error")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))
    current_app.repo.reopen_ticket(ticket_id, reason, current_user())
    flash("Ticket reopened.", "success")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@tickets_bp.route("/cancel/<ticket_id>", methods=["POST"])
@login_required
def cancel_ticket(ticket_id):
    ticket = visible_ticket_or_redirect(ticket_id)
    if not ticket or ticket["createdBy"] != current_user()["uid"]:
        flash("This ticket cannot be cancelled.", "error")
        return redirect(url_for("tickets.all_tickets"))
    current_app.repo.cancel_ticket(ticket_id, request.form.get("reason", ""), current_user())
    flash("Ticket cancelled.", "success")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    if request.method == "POST":
        password = request.form.get("password", "")
        if password and len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("profile/index.html", user=user)
        current_app.repo.update_profile(
            user["uid"],
            {
                "mobileNo": request.form.get("mobileNo", "").strip(),
                "notificationEmail": request.form.get("notificationEmail") == "on",
                "notificationInApp": request.form.get("notificationInApp") == "on",
                "password": password,
            },
            user,
        )
        flash("Profile updated.", "success")
        return redirect(url_for("profile.profile"))
    return render_template("profile/index.html", user=user)


@settings_bp.route("/settings")
@login_required
def settings():
    return render_template("settings/index.html")


@settings_bp.route("/audit-log")
@login_required
@permission_required("canManageUsers")
def audit_log():
    return render_template("settings/audit_log.html", audit_logs=current_app.repo.audit_logs())


@errors_bp.route("/unauthorized")
def unauthorized():
    return render_template("errors/unauthorized.html"), 403
