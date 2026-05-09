import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from werkzeug.security import generate_password_hash

from app.constants import (
    AREA_SEED,
    CATEGORY_SEED,
    PERMISSIONS,
    SYSTEM_SEED,
    TEAM_SEED,
)
from app.services.seed import build_seed_data


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class JsonRepository:
    def __init__(self, path):
        candidate = Path(path)
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            self.path = candidate
        except OSError:
            # Read-only filesystem (e.g. Vercel /var/task). Use /tmp instead so
            # the app at least boots. Note: data here is ephemeral per invocation.
            import os
            tmp = Path(os.environ.get("TMPDIR", "/tmp")) / "kg_ticket_store.json"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            self.path = tmp
        if not self.path.exists():
            self._write(build_seed_data())
        else:
            self._ensure_schema()

    def _read(self):
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, data):
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    def _ensure_schema(self):
        data = self._read()
        seed = build_seed_data()
        changed = False
        for key, value in seed.items():
            if key not in data:
                data[key] = value
                changed = True

        existing_user_ids = {user["uid"] for user in data.get("users", [])}
        for user in seed["users"]:
            if user["uid"] not in existing_user_ids:
                data["users"].append(user)
                changed = True

        existing_permission_ids = set(data.get("userPermissions", {}).keys())
        for uid, permissions in seed["userPermissions"].items():
            if uid not in existing_permission_ids:
                data["userPermissions"][uid] = permissions
                changed = True

        if "ticketCounters" not in data or "default" not in data["ticketCounters"]:
            data["ticketCounters"] = seed["ticketCounters"]
            changed = True

        if changed:
            self._write(data)

    def all_data(self):
        return self._read()

    def save_data(self, data):
        self._write(data)

    def user_types(self):
        return sorted(self._read()["userTypes"], key=lambda item: item.get("sortOrder", 999))

    def roles(self):
        return self._read()["roles"]

    def departments(self):
        return self._read()["departments"]

    def systems(self):
        return [item for item in self._read()["systems"] if item.get("isActive")]

    def categories(self):
        return [item for item in self._read()["categories"] if item.get("isActive")]

    def areas(self, system_id=None):
        areas = [item for item in self._read()["areas"] if item.get("isActive")]
        if system_id:
            return [area for area in areas if area["systemId"] == system_id]
        return areas

    def teams(self, system_id=None):
        teams = [item for item in self._read()["teams"] if item.get("isActive")]
        if system_id:
            return [team for team in teams if team["systemId"] == system_id]
        return teams

    def get_system(self, system_id):
        return next((item for item in self._read()["systems"] if item["id"] == system_id), None)

    def get_category(self, category_id):
        return next((item for item in self._read()["categories"] if item["id"] == category_id), None)

    def get_area(self, area_id):
        return next((item for item in self._read()["areas"] if item["id"] == area_id), None)

    def get_team(self, team_id):
        return next((item for item in self._read()["teams"] if item["id"] == team_id), None)

    def users(self, include_deleted=False):
        users = self._read()["users"]
        if include_deleted:
            return users
        return [user for user in users if not user.get("isDeleted")]

    def active_users(self):
        return [
            user
            for user in self.users()
            if user.get("isActive") and not user.get("isDeleted")
        ]

    def get_user(self, uid):
        return next((user for user in self._read()["users"] if user["uid"] == uid), None)

    def get_user_by_email(self, email):
        normalized = email.strip().lower()
        return next(
            (
                user
                for user in self._read()["users"]
                if user["email"].strip().lower() == normalized
            ),
            None,
        )

    def get_permissions(self, uid):
        data = self._read()
        permissions = data["userPermissions"].get(uid, {})
        return {key: bool(permissions.get(key, False)) for key, _ in PERMISSIONS}

    def create_user(self, payload, permissions, actor):
        data = self._read()
        if self.get_user_by_email(payload["email"]):
            raise ValueError("Email already exists.")

        now = utc_now()
        uid = new_id("uid")
        user = {
            "uid": uid,
            "employeeCode": payload["employeeCode"],
            "fullName": payload["fullName"],
            "email": payload["email"].strip().lower(),
            "passwordHash": generate_password_hash(payload["password"]),
            "mobileNo": payload.get("mobileNo", ""),
            "departmentId": payload.get("departmentId", ""),
            "designation": payload.get("designation", ""),
            "reportingManagerId": payload.get("reportingManagerId", ""),
            "userTypeId": payload.get("userTypeId", ""),
            "roleId": payload.get("roleId", ""),
            "systemAccess": payload.get("systemAccess", []),
            "defaultDashboard": payload.get("defaultDashboard", "requester"),
            "isActive": payload.get("isActive", False),
            "isDeleted": False,
            "notificationEmail": payload.get("notificationEmail", False),
            "notificationInApp": payload.get("notificationInApp", False),
            "createdAt": now,
            "createdBy": actor["uid"],
            "updatedAt": now,
            "updatedBy": actor["uid"],
            "deletedAt": None,
            "deletedBy": None,
        }
        data["users"].append(user)
        data["userPermissions"][uid] = {
            "userId": uid,
            **permissions,
            "updatedAt": now,
            "updatedBy": actor["uid"],
        }
        self._audit(
            data,
            "User",
            "CREATE_USER",
            uid,
            None,
            {"fullName": user["fullName"], "email": user["email"]},
            actor,
        )
        self._write(data)
        return user

    def update_user(self, uid, payload, permissions, actor):
        data = self._read()
        index = next((i for i, user in enumerate(data["users"]) if user["uid"] == uid), None)
        if index is None:
            raise ValueError("User not found.")

        user = data["users"][index]
        old_value = deepcopy(user)
        now = utc_now()
        editable_fields = [
            "fullName",
            "mobileNo",
            "departmentId",
            "designation",
            "reportingManagerId",
            "userTypeId",
            "roleId",
            "systemAccess",
            "defaultDashboard",
            "isActive",
            "notificationEmail",
            "notificationInApp",
        ]
        for field in editable_fields:
            if field in payload:
                user[field] = payload[field]

        if payload.get("password"):
            user["passwordHash"] = generate_password_hash(payload["password"])

        user["updatedAt"] = now
        user["updatedBy"] = actor["uid"]
        data["users"][index] = user
        data["userPermissions"][uid] = {
            "userId": uid,
            **permissions,
            "updatedAt": now,
            "updatedBy": actor["uid"],
        }
        self._audit(
            data,
            "User",
            "UPDATE_USER",
            uid,
            old_value,
            {"fullName": user["fullName"], "email": user["email"]},
            actor,
        )
        self._audit(
            data,
            "User",
            "UPDATE_PERMISSION",
            uid,
            None,
            permissions,
            actor,
        )
        self._write(data)
        return user

    def set_user_active(self, uid, is_active, actor):
        data = self._read()
        user = next((entry for entry in data["users"] if entry["uid"] == uid), None)
        if not user:
            raise ValueError("User not found.")
        old_value = deepcopy(user)
        user["isActive"] = is_active
        user["updatedAt"] = utc_now()
        user["updatedBy"] = actor["uid"]
        self._audit(
            data,
            "User",
            "ACTIVATE_USER" if is_active else "DEACTIVATE_USER",
            uid,
            old_value,
            {"isActive": is_active},
            actor,
        )
        self._write(data)

    def soft_delete_user(self, uid, actor):
        data = self._read()
        user = next((entry for entry in data["users"] if entry["uid"] == uid), None)
        if not user:
            raise ValueError("User not found.")
        old_value = deepcopy(user)
        now = utc_now()
        user["isDeleted"] = True
        user["isActive"] = False
        user["deletedAt"] = now
        user["deletedBy"] = actor["uid"]
        user["updatedAt"] = now
        user["updatedBy"] = actor["uid"]
        self._audit(
            data,
            "User",
            "DELETE_USER",
            uid,
            old_value,
            {"isDeleted": True, "isActive": False},
            actor,
        )
        self._write(data)

    def update_profile(self, uid, payload, actor):
        data = self._read()
        user = next((entry for entry in data["users"] if entry["uid"] == uid), None)
        if not user:
            raise ValueError("User not found.")
        old_value = deepcopy(user)
        user["mobileNo"] = payload.get("mobileNo", user.get("mobileNo", ""))
        user["notificationEmail"] = payload.get("notificationEmail", False)
        user["notificationInApp"] = payload.get("notificationInApp", False)
        if payload.get("password"):
            user["passwordHash"] = generate_password_hash(payload["password"])
        user["updatedAt"] = utc_now()
        user["updatedBy"] = actor["uid"]
        self._audit(
            data,
            "User",
            "UPDATE_USER",
            uid,
            old_value,
            {"profile": True},
            actor,
        )
        self._write(data)

    def tickets(self):
        return sorted(
            [ticket for ticket in self._read()["tickets"] if not ticket.get("isDeleted")],
            key=lambda item: item.get("updatedAt", ""),
            reverse=True,
        )

    def get_ticket(self, ticket_id):
        return next(
            (
                ticket
                for ticket in self._read()["tickets"]
                if ticket["id"] == ticket_id and not ticket.get("isDeleted")
            ),
            None,
        )

    def visible_tickets(self, actor, permissions):
        tickets = self.tickets()
        if permissions.get("canViewAllTickets") or permissions.get("canManageUsers"):
            return tickets

        team_ids = {
            team["id"]
            for team in self.teams()
            if team.get("teamLeadId") == actor["uid"] or actor["uid"] in team.get("memberIds", [])
        }
        visible = []
        for ticket in tickets:
            if permissions.get("canViewOwnTicket") and ticket.get("createdBy") == actor["uid"]:
                visible.append(ticket)
            elif ticket.get("authorizedPersonId") == actor["uid"]:
                visible.append(ticket)
            elif ticket.get("assignedTeamId") in team_ids:
                visible.append(ticket)
            elif ticket.get("assignedTo") == actor["uid"]:
                visible.append(ticket)
        return visible

    def ticket_notes(self, ticket_id, include_internal=False):
        notes = [
            note
            for note in self._read()["ticketNotes"]
            if note["ticketId"] == ticket_id and not note.get("isDeleted")
        ]
        if not include_internal:
            notes = [note for note in notes if note.get("visibility") == "Public"]
        return sorted(notes, key=lambda item: item.get("createdAt", ""), reverse=True)

    def ticket_status_history(self, ticket_id):
        return sorted(
            [
                item
                for item in self._read()["ticketStatusHistory"]
                if item["ticketId"] == ticket_id
            ],
            key=lambda item: item.get("changedAt", ""),
            reverse=True,
        )

    def ticket_attachments(self, ticket_id):
        return [
            item
            for item in self._read()["ticketAttachments"]
            if item["ticketId"] == ticket_id and not item.get("isDeleted")
        ]

    def create_ticket(self, payload, actor, submit=True):
        data = self._read()
        now = utc_now()
        ticket_id = new_id("ticket")
        ticket_no = self._next_ticket_no(data)
        system = self._required_master(data["systems"], payload["systemId"], "System")
        category = self._required_master(data["categories"], payload["categoryId"], "Category")
        area = self._required_master(data["areas"], payload["areaId"], "Area")
        if area["systemId"] != system["id"]:
            raise ValueError("Selected area does not belong to selected system.")
        authorized_person = self._find_authorized_person(data, system, area)
        status = "Pending Authorization" if submit else "Draft"

        custom_area = (payload.get("customAreaName") or "").strip()
        effective_area_name = custom_area if custom_area else area["name"]
        ticket = {
            "id": ticket_id,
            "ticketNo": ticket_no,
            "systemId": system["id"],
            "systemName": system["name"],
            "categoryId": category["id"],
            "categoryName": category["name"],
            "areaId": area["id"],
            "areaName": effective_area_name,
            "customAreaName": custom_area or None,
            "priority": payload["priority"],
            "title": payload["title"],
            "description": payload["description"],
            "status": status,
            "createdBy": actor["uid"],
            "createdByName": actor["fullName"],
            "createdByEmail": actor["email"],
            "createdAt": now,
            "authorizedPersonId": authorized_person["uid"] if authorized_person else None,
            "authorizedPersonName": authorized_person["fullName"] if authorized_person else None,
            "approvedBy": None,
            "approvedByName": None,
            "approvedAt": None,
            "rejectedBy": None,
            "rejectedByName": None,
            "rejectedAt": None,
            "rejectionReason": None,
            "assignedTeamId": None,
            "assignedTeamName": None,
            "assignedTo": None,
            "assignedToName": None,
            "expectedDate": payload.get("expectedDate") or None,
            "dueDate": None,
            "completedBy": None,
            "completedByName": None,
            "completedAt": None,
            "closedBy": None,
            "closedByName": None,
            "closedAt": None,
            "reopenCount": 0,
            "isDeleted": False,
            "updatedAt": now,
            "updatedBy": actor["uid"],
        }
        data["tickets"].append(ticket)
        self._status_history(data, ticket, None, status, actor, "Ticket created.")
        self._ticket_note(
            data,
            ticket,
            "User Comment",
            payload["description"],
            "Public",
            actor,
        )
        if payload.get("attachmentName"):
            self._ticket_attachment(data, ticket, payload["attachmentName"], actor)
        self._audit(
            data,
            "Ticket",
            "SUBMIT_TICKET" if submit else "CREATE_TICKET",
            ticket_id,
            None,
            {"status": status, "title": ticket["title"]},
            actor,
            record_no=ticket_no,
        )
        if submit and authorized_person:
            self._notify(
                data,
                receiver_id=authorized_person["uid"],
                title=f"New ticket waiting for approval",
                message=f"{ticket_no} from {actor['fullName']}: {ticket['title']}",
                ticket=ticket,
                notification_type="ticket_created",
                actor=actor,
            )
        self._write(data)
        return ticket

    def update_ticket(self, ticket_id, payload, actor, submit=False):
        data, ticket = self._ticket_for_update(ticket_id)
        if ticket["status"] not in ["Draft", "Need More Information"]:
            raise ValueError("Ticket can only be edited while draft or needing more information.")
        old_value = deepcopy(ticket)
        system = self._required_master(data["systems"], payload["systemId"], "System")
        category = self._required_master(data["categories"], payload["categoryId"], "Category")
        area = self._required_master(data["areas"], payload["areaId"], "Area")
        if area["systemId"] != system["id"]:
            raise ValueError("Selected area does not belong to selected system.")
        authorized_person = self._find_authorized_person(data, system, area)
        old_status = ticket["status"]

        custom_area = (payload.get("customAreaName") or "").strip()
        effective_area_name = custom_area if custom_area else area["name"]
        ticket.update(
            {
                "systemId": system["id"],
                "systemName": system["name"],
                "categoryId": category["id"],
                "categoryName": category["name"],
                "areaId": area["id"],
                "areaName": effective_area_name,
                "customAreaName": custom_area or None,
                "priority": payload["priority"],
                "title": payload["title"],
                "description": payload["description"],
                "expectedDate": payload.get("expectedDate") or None,
                "authorizedPersonId": authorized_person["uid"] if authorized_person else None,
                "authorizedPersonName": authorized_person["fullName"] if authorized_person else None,
                "updatedAt": utc_now(),
                "updatedBy": actor["uid"],
            }
        )
        if submit:
            ticket["status"] = "Pending Authorization"
            self._status_history(data, ticket, old_status, ticket["status"], actor, "Ticket submitted for authorization.")
        if payload.get("attachmentName"):
            self._ticket_attachment(data, ticket, payload["attachmentName"], actor)
        self._audit(
            data,
            "Ticket",
            "SUBMIT_TICKET" if submit else "UPDATE_TICKET",
            ticket_id,
            old_value,
            {"status": ticket["status"], "title": ticket["title"]},
            actor,
            record_no=ticket["ticketNo"],
        )
        self._write(data)
        return ticket

    def approve_ticket(self, ticket_id, team_id, due_date, note, actor):
        data, ticket = self._ticket_for_update(ticket_id)
        team = self._required_master(data["teams"], team_id, "Team")
        now = utc_now()
        old_status = ticket["status"]
        ticket.update(
            {
                "status": "Approved",
                "approvedBy": actor["uid"],
                "approvedByName": actor["fullName"],
                "approvedAt": now,
                "assignedTeamId": team["id"],
                "assignedTeamName": team["name"],
                "dueDate": due_date or None,
                "updatedAt": now,
                "updatedBy": actor["uid"],
            }
        )
        self._ticket_note(data, ticket, "Approval Note", note or "Ticket approved.", "Internal", actor)
        self._status_history(data, ticket, old_status, "Approved", actor, note or "Ticket approved.")
        self._audit(data, "Ticket", "APPROVE_TICKET", ticket_id, {"status": old_status}, {"status": "Approved"}, actor, record_no=ticket["ticketNo"])
        # notify creator + team lead
        self._notify(data, receiver_id=ticket.get("createdBy"),
                     title="Ticket approved",
                     message=f"{ticket['ticketNo']} approved and routed to {team['name']}.",
                     ticket=ticket, notification_type="ticket_approved", actor=actor)
        lead_id = self._team_lead_id(data, team["id"])
        if lead_id:
            self._notify(data, receiver_id=lead_id,
                         title="New work for your team",
                         message=f"{ticket['ticketNo']} approved and assigned to {team['name']}.",
                         ticket=ticket, notification_type="team_assigned", actor=actor)
        self._write(data)
        return ticket

    def reject_ticket(self, ticket_id, reason, actor):
        data, ticket = self._ticket_for_update(ticket_id)
        now = utc_now()
        old_status = ticket["status"]
        ticket.update(
            {
                "status": "Rejected",
                "rejectedBy": actor["uid"],
                "rejectedByName": actor["fullName"],
                "rejectedAt": now,
                "rejectionReason": reason,
                "updatedAt": now,
                "updatedBy": actor["uid"],
            }
        )
        self._ticket_note(data, ticket, "Rejection Note", reason, "Public", actor)
        self._status_history(data, ticket, old_status, "Rejected", actor, reason)
        self._audit(data, "Ticket", "REJECT_TICKET", ticket_id, {"status": old_status}, {"status": "Rejected"}, actor, record_no=ticket["ticketNo"])
        self._notify(data, receiver_id=ticket.get("createdBy"),
                     title="Ticket rejected",
                     message=f"{ticket['ticketNo']} rejected: {reason}",
                     ticket=ticket, notification_type="ticket_rejected", actor=actor)
        self._write(data)
        return ticket

    def request_more_info(self, ticket_id, note, actor):
        data, ticket = self._ticket_for_update(ticket_id)
        old_status = ticket["status"]
        ticket["status"] = "Need More Information"
        ticket["updatedAt"] = utc_now()
        ticket["updatedBy"] = actor["uid"]
        self._ticket_note(data, ticket, "More Information Note", note, "Public", actor)
        self._status_history(data, ticket, old_status, "Need More Information", actor, note)
        self._audit(data, "Ticket", "NEED_MORE_INFORMATION", ticket_id, {"status": old_status}, {"status": "Need More Information"}, actor, record_no=ticket["ticketNo"])
        self._notify(data, receiver_id=ticket.get("createdBy"),
                     title="Need your reply",
                     message=f"{ticket['ticketNo']} sent back: {note}",
                     ticket=ticket, notification_type="more_info", actor=actor)
        self._write(data)
        return ticket

    def assign_member(self, ticket_id, member_id, note, actor):
        data, ticket = self._ticket_for_update(ticket_id)
        member = self._required_master(data["users"], member_id, "Member", id_key="uid")
        old_status = ticket["status"]
        ticket.update(
            {
                "status": "Assigned To Team",
                "assignedTo": member["uid"],
                "assignedToName": member["fullName"],
                "updatedAt": utc_now(),
                "updatedBy": actor["uid"],
            }
        )
        self._ticket_note(data, ticket, "Internal Note", note or f"Assigned to {member['fullName']}.", "Internal", actor)
        self._status_history(data, ticket, old_status, "Assigned To Team", actor, note or "Team member assigned.")
        self._audit(data, "Ticket", "ASSIGN_MEMBER", ticket_id, {"status": old_status}, {"assignedTo": member["uid"]}, actor, record_no=ticket["ticketNo"])
        self._notify(data, receiver_id=member["uid"],
                     title="Ticket assigned to you",
                     message=f"{ticket['ticketNo']} assigned to you: {ticket['title']}",
                     ticket=ticket, notification_type="member_assigned", actor=actor)
        self._write(data)
        return ticket

    def start_work(self, ticket_id, note, actor):
        data, ticket = self._ticket_for_update(ticket_id)
        old_status = ticket["status"]
        ticket["status"] = "In Progress"
        ticket["updatedAt"] = utc_now()
        ticket["updatedBy"] = actor["uid"]
        self._ticket_note(data, ticket, "Work Note", note or "Work started.", "Public", actor)
        self._status_history(data, ticket, old_status, "In Progress", actor, note or "Work started.")
        self._audit(data, "Ticket", "UPDATE_STATUS", ticket_id, {"status": old_status}, {"status": "In Progress"}, actor, record_no=ticket["ticketNo"])
        self._notify(data, receiver_id=ticket.get("createdBy"),
                     title="Work started on your ticket",
                     message=f"{ticket['ticketNo']}: {ticket['title']}",
                     ticket=ticket, notification_type="work_started", actor=actor)
        self._notify(data, receiver_id=ticket.get("authorizedPersonId"),
                     title="Team started work",
                     message=f"{ticket['ticketNo']} is now in progress.",
                     ticket=ticket, notification_type="work_started", actor=actor)
        self._write(data)
        return ticket

    def add_ticket_note(self, ticket_id, note_type, note_text, visibility, actor):
        data, ticket = self._ticket_for_update(ticket_id)
        self._ticket_note(data, ticket, note_type, note_text, visibility, actor)
        ticket["updatedAt"] = utc_now()
        ticket["updatedBy"] = actor["uid"]
        self._audit(data, "Ticket", "ADD_NOTE", ticket_id, None, {"noteType": note_type}, actor, record_no=ticket["ticketNo"])
        self._write(data)
        return ticket

    def complete_ticket(self, ticket_id, resolution_note, actor):
        data, ticket = self._ticket_for_update(ticket_id)
        old_status = ticket["status"]
        now = utc_now()
        ticket.update(
            {
                "status": "Completed",
                "completedBy": actor["uid"],
                "completedByName": actor["fullName"],
                "completedAt": now,
                "updatedAt": now,
                "updatedBy": actor["uid"],
            }
        )
        self._ticket_note(data, ticket, "Resolution Note", resolution_note, "Public", actor)
        self._status_history(data, ticket, old_status, "Completed", actor, resolution_note)
        self._audit(data, "Ticket", "COMPLETE_TICKET", ticket_id, {"status": old_status}, {"status": "Completed"}, actor, record_no=ticket["ticketNo"])
        self._notify(data, receiver_id=ticket.get("authorizedPersonId"),
                     title="Work done — needs closure",
                     message=f"{ticket['ticketNo']} marked done: {resolution_note}",
                     ticket=ticket, notification_type="ticket_done", actor=actor)
        self._notify(data, receiver_id=ticket.get("createdBy"),
                     title="Your ticket is done",
                     message=f"{ticket['ticketNo']}: {ticket['title']}",
                     ticket=ticket, notification_type="ticket_done", actor=actor)
        self._write(data)
        return ticket

    def close_ticket(self, ticket_id, closure_note, actor):
        data, ticket = self._ticket_for_update(ticket_id)
        old_status = ticket["status"]
        now = utc_now()
        ticket.update(
            {
                "status": "Closed",
                "closedBy": actor["uid"],
                "closedByName": actor["fullName"],
                "closedAt": now,
                "updatedAt": now,
                "updatedBy": actor["uid"],
            }
        )
        self._ticket_note(data, ticket, "Closure Note", closure_note or "Ticket closed.", "Public", actor)
        self._status_history(data, ticket, old_status, "Closed", actor, closure_note or "Ticket closed.")
        self._audit(data, "Ticket", "CLOSE_TICKET", ticket_id, {"status": old_status}, {"status": "Closed"}, actor, record_no=ticket["ticketNo"])
        self._notify(data, receiver_id=ticket.get("createdBy"),
                     title="Ticket closed",
                     message=f"{ticket['ticketNo']} closed: {ticket['title']}",
                     ticket=ticket, notification_type="ticket_closed", actor=actor)
        if ticket.get("assignedTo"):
            self._notify(data, receiver_id=ticket.get("assignedTo"),
                         title="Ticket closed",
                         message=f"{ticket['ticketNo']} has been verified and closed.",
                         ticket=ticket, notification_type="ticket_closed", actor=actor)
        self._write(data)
        return ticket

    def reopen_ticket(self, ticket_id, reason, actor):
        data, ticket = self._ticket_for_update(ticket_id)
        old_status = ticket["status"]
        ticket["status"] = "Reopened"
        ticket["reopenCount"] = int(ticket.get("reopenCount") or 0) + 1
        ticket["updatedAt"] = utc_now()
        ticket["updatedBy"] = actor["uid"]
        self._ticket_note(data, ticket, "Reopen Note", reason, "Public", actor)
        self._status_history(data, ticket, old_status, "Reopened", actor, reason)
        self._audit(data, "Ticket", "REOPEN_TICKET", ticket_id, {"status": old_status}, {"status": "Reopened"}, actor, record_no=ticket["ticketNo"])
        self._notify(data, receiver_id=ticket.get("authorizedPersonId"),
                     title="Ticket reopened",
                     message=f"{ticket['ticketNo']} reopened by {actor['fullName']}: {reason}",
                     ticket=ticket, notification_type="ticket_reopened", actor=actor)
        if ticket.get("assignedTo"):
            self._notify(data, receiver_id=ticket.get("assignedTo"),
                         title="Ticket reopened",
                         message=f"{ticket['ticketNo']} reopened — needs review.",
                         ticket=ticket, notification_type="ticket_reopened", actor=actor)
        self._write(data)
        return ticket

    def cancel_ticket(self, ticket_id, reason, actor):
        data, ticket = self._ticket_for_update(ticket_id)
        old_status = ticket["status"]
        ticket["status"] = "Cancelled"
        ticket["updatedAt"] = utc_now()
        ticket["updatedBy"] = actor["uid"]
        self._ticket_note(data, ticket, "User Comment", reason or "Ticket cancelled.", "Public", actor)
        self._status_history(data, ticket, old_status, "Cancelled", actor, reason or "Ticket cancelled.")
        self._audit(data, "Ticket", "DELETE_TICKET", ticket_id, {"status": old_status}, {"status": "Cancelled"}, actor, record_no=ticket["ticketNo"])
        self._write(data)
        return ticket

    # ─── NOTIFICATIONS ─────────────────────────────────────────────
    def notifications_for_user(self, uid, limit=20, only_unread=False):
        """Return notifications for a given user, newest first."""
        if not uid:
            return []
        items = [
            n for n in self._read().get("notifications", [])
            if n.get("receiverId") == uid
        ]
        if only_unread:
            items = [n for n in items if not n.get("isRead")]
        items.sort(key=lambda n: n.get("createdAt", ""), reverse=True)
        if limit:
            items = items[:limit]
        return items

    def unread_notification_count(self, uid):
        if not uid:
            return 0
        return sum(
            1 for n in self._read().get("notifications", [])
            if n.get("receiverId") == uid and not n.get("isRead")
        )

    def mark_notification_read(self, notification_id, uid):
        data = self._read()
        for n in data.get("notifications", []):
            if n.get("id") == notification_id and n.get("receiverId") == uid:
                n["isRead"] = True
                n["readAt"] = utc_now()
                self._write(data)
                return True
        return False

    def mark_all_notifications_read(self, uid):
        data = self._read()
        changed = 0
        for n in data.get("notifications", []):
            if n.get("receiverId") == uid and not n.get("isRead"):
                n["isRead"] = True
                n["readAt"] = utc_now()
                changed += 1
        if changed:
            self._write(data)
        return changed

    def _notify(self, data, *, receiver_id, title, message, ticket=None, notification_type="ticket", actor=None):
        if not receiver_id or actor and receiver_id == actor.get("uid"):
            # Don't notify users about their own actions.
            return
        if "notifications" not in data:
            data["notifications"] = []
        data["notifications"].append({
            "id": new_id("notif"),
            "receiverId": receiver_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "ticketId": (ticket or {}).get("id"),
            "ticketNo": (ticket or {}).get("ticketNo"),
            "createdBy": (actor or {}).get("uid", "system"),
            "createdByName": (actor or {}).get("fullName", "System"),
            "isRead": False,
            "readAt": None,
            "createdAt": utc_now(),
        })

    def _team_lead_id(self, data, team_id):
        team = next((t for t in data.get("teams", []) if t.get("id") == team_id), None)
        return (team or {}).get("teamLeadId")

    def audit_logs(self):
        return sorted(
            self._read()["auditLogs"],
            key=lambda item: item.get("createdAt", ""),
            reverse=True,
        )

    def _next_ticket_no(self, data):
        counter = data["ticketCounters"]["default"]
        counter["lastTicketNo"] = int(counter.get("lastTicketNo", 0)) + 1
        counter["updatedAt"] = utc_now()
        return f"{counter.get('prefix', 'KG-TKT')}-{counter['lastTicketNo']:06d}"

    def _required_master(self, items, item_id, label, id_key="id"):
        item = next((entry for entry in items if entry[id_key] == item_id), None)
        if not item:
            raise ValueError(f"{label} not found.")
        return item

    def _find_authorized_person(self, data, system, area):
        candidate_ids = area.get("authorizedPersonIds") or system.get("authorizedPersonIds") or []
        for uid in candidate_ids:
            user = next(
                (
                    item
                    for item in data["users"]
                    if item["uid"] == uid and item.get("isActive") and not item.get("isDeleted")
                ),
                None,
            )
            if user:
                return user
        return next((user for user in data["users"] if user.get("roleId") == "role_admin"), None)

    def _ticket_for_update(self, ticket_id):
        data = self._read()
        ticket = next(
            (
                item
                for item in data["tickets"]
                if item["id"] == ticket_id and not item.get("isDeleted")
            ),
            None,
        )
        if not ticket:
            raise ValueError("Ticket not found.")
        return data, ticket

    def _ticket_note(self, data, ticket, note_type, note_text, visibility, actor):
        if not note_text:
            return
        data["ticketNotes"].append(
            {
                "id": new_id("note"),
                "ticketId": ticket["id"],
                "ticketNo": ticket["ticketNo"],
                "noteType": note_type,
                "noteText": note_text,
                "visibility": visibility,
                "createdBy": actor["uid"],
                "createdByName": actor["fullName"],
                "createdAt": utc_now(),
                "isDeleted": False,
            }
        )

    def _ticket_attachment(self, data, ticket, file_name, actor):
        data["ticketAttachments"].append(
            {
                "id": new_id("attachment"),
                "ticketId": ticket["id"],
                "ticketNo": ticket["ticketNo"],
                "fileName": file_name,
                "fileUrl": "",
                "fileType": "",
                "fileSize": 0,
                "uploadedBy": actor["uid"],
                "uploadedByName": actor["fullName"],
                "uploadedAt": utc_now(),
                "isDeleted": False,
            }
        )

    def _status_history(self, data, ticket, old_status, new_status, actor, note):
        data["ticketStatusHistory"].append(
            {
                "id": new_id("history"),
                "ticketId": ticket["id"],
                "ticketNo": ticket["ticketNo"],
                "oldStatus": old_status,
                "newStatus": new_status,
                "changedBy": actor["uid"],
                "changedByName": actor["fullName"],
                "changeNote": note,
                "changedAt": utc_now(),
            }
        )

    def _set_ticket_status(self, ticket_id, status, audit_action, note, note_type, actor):
        data, ticket = self._ticket_for_update(ticket_id)
        old_status = ticket["status"]
        ticket["status"] = status
        ticket["updatedAt"] = utc_now()
        ticket["updatedBy"] = actor["uid"]
        self._ticket_note(data, ticket, note_type, note, "Public", actor)
        self._status_history(data, ticket, old_status, status, actor, note)
        self._audit(data, "Ticket", audit_action, ticket_id, {"status": old_status}, {"status": status}, actor, record_no=ticket["ticketNo"])
        self._write(data)
        return ticket

    def _audit(self, data, module, action, record_id, old_value, new_value, actor, record_no=None):
        data["auditLogs"].append(
            {
                "id": new_id("audit"),
                "module": module,
                "action": action,
                "recordId": record_id,
                "recordNo": record_no,
                "oldValue": old_value,
                "newValue": new_value,
                "createdBy": actor["uid"],
                "createdByName": actor.get("fullName", "System"),
                "createdAt": utc_now(),
            }
        )
