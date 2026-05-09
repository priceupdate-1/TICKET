from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app.constants import (
    ADMIN_PERMISSIONS,
    APPROVER_PERMISSIONS,
    AREA_SEED,
    CATEGORY_SEED,
    DEPARTMENT_SEED,
    ROLE_SEED,
    REQUEST_USER_PERMISSIONS,
    SYSTEM_SEED,
    TEAM_LEAD_PERMISSIONS,
    TEAM_MEMBER_PERMISSIONS,
    TEAM_SEED,
    USER_TYPE_SEED,
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def build_seed_data():
    now = utc_now()

    users = [
        {
            "uid": "admin_uid",
            "employeeCode": "KG001",
            "fullName": "Admin User",
            "email": "admin@company.com",
            "passwordHash": generate_password_hash("Admin@123"),
            "mobileNo": "9999999999",
            "departmentId": "dept_it",
            "designation": "System Admin",
            "reportingManagerId": "",
            "userTypeId": "ut_admin",
            "roleId": "role_admin",
            "systemAccess": ["Lattice", "Trybe"],
            "defaultDashboard": "admin",
            "isActive": True,
            "isDeleted": False,
            "notificationEmail": True,
            "notificationInApp": True,
            "createdAt": now,
            "createdBy": "system",
            "updatedAt": now,
            "updatedBy": "system",
            "deletedAt": None,
            "deletedBy": None,
        },
        {
            "uid": "requester_uid",
            "employeeCode": "KG002",
            "fullName": "Request User",
            "email": "requester@company.com",
            "passwordHash": generate_password_hash("Request@123"),
            "mobileNo": "9000000001",
            "departmentId": "dept_sales",
            "designation": "Requester",
            "reportingManagerId": "admin_uid",
            "userTypeId": "ut_request_user",
            "roleId": "role_requester",
            "systemAccess": ["Lattice", "Trybe"],
            "defaultDashboard": "requester",
            "isActive": True,
            "isDeleted": False,
            "notificationEmail": True,
            "notificationInApp": True,
            "createdAt": now,
            "createdBy": "system",
            "updatedAt": now,
            "updatedBy": "system",
            "deletedAt": None,
            "deletedBy": None,
        },
        {
            "uid": "approver_uid",
            "employeeCode": "KG003",
            "fullName": "Authorized User",
            "email": "approver@company.com",
            "passwordHash": generate_password_hash("Approve@123"),
            "mobileNo": "9000000002",
            "departmentId": "dept_management",
            "designation": "Authorized Person",
            "reportingManagerId": "admin_uid",
            "userTypeId": "ut_authorized_person",
            "roleId": "role_approver",
            "systemAccess": ["Lattice", "Trybe"],
            "defaultDashboard": "approver",
            "isActive": True,
            "isDeleted": False,
            "notificationEmail": True,
            "notificationInApp": True,
            "createdAt": now,
            "createdBy": "system",
            "updatedAt": now,
            "updatedBy": "system",
            "deletedAt": None,
            "deletedBy": None,
        },
        {
            "uid": "teamlead_uid",
            "employeeCode": "KG004",
            "fullName": "Team Lead User",
            "email": "teamlead@company.com",
            "passwordHash": generate_password_hash("Teamlead@123"),
            "mobileNo": "9000000003",
            "departmentId": "dept_it",
            "designation": "Team Lead",
            "reportingManagerId": "admin_uid",
            "userTypeId": "ut_team_lead",
            "roleId": "role_team_lead",
            "systemAccess": ["Lattice", "Trybe"],
            "defaultDashboard": "team",
            "isActive": True,
            "isDeleted": False,
            "notificationEmail": True,
            "notificationInApp": True,
            "createdAt": now,
            "createdBy": "system",
            "updatedAt": now,
            "updatedBy": "system",
            "deletedAt": None,
            "deletedBy": None,
        },
        {
            "uid": "member_uid",
            "employeeCode": "KG005",
            "fullName": "Team Member User",
            "email": "member@company.com",
            "passwordHash": generate_password_hash("Member@123"),
            "mobileNo": "9000000004",
            "departmentId": "dept_data",
            "designation": "Work Team Member",
            "reportingManagerId": "teamlead_uid",
            "userTypeId": "ut_team_member",
            "roleId": "role_team_member",
            "systemAccess": ["Lattice", "Trybe"],
            "defaultDashboard": "team",
            "isActive": True,
            "isDeleted": False,
            "notificationEmail": True,
            "notificationInApp": True,
            "createdAt": now,
            "createdBy": "system",
            "updatedAt": now,
            "updatedBy": "system",
            "deletedAt": None,
            "deletedBy": None,
        },
    ]

    user_types = [
        {
            "id": item_id,
            "name": name,
            "code": code,
            "description": description,
            "isActive": True,
            "sortOrder": sort_order,
            "createdAt": now,
            "createdBy": "system",
        }
        for item_id, name, code, description, sort_order in USER_TYPE_SEED
    ]

    roles = [
        {
            "id": item_id,
            "name": name,
            "code": code,
            "description": description,
            "isActive": True,
            "createdAt": now,
            "createdBy": "system",
        }
        for item_id, name, code, description in ROLE_SEED
    ]

    departments = [
        {
            "id": item_id,
            "name": name,
            "code": code,
            "isActive": True,
            "createdAt": now,
            "createdBy": "system",
        }
        for item_id, name, code in DEPARTMENT_SEED
    ]

    categories = [
        {
            "id": item_id,
            "name": name,
            "code": code,
            "isActive": True,
            "createdAt": now,
            "createdBy": "system",
        }
        for item_id, name, code in CATEGORY_SEED
    ]

    areas = [
        {
            "id": item_id,
            "systemId": system_id,
            "systemName": system_name,
            "name": name,
            "code": code,
            "authorizedPersonIds": ["approver_uid"],
            "defaultTeamId": default_team_id,
            "isActive": True,
            "createdAt": now,
            "createdBy": "system",
        }
        for item_id, system_id, system_name, name, code, default_team_id in AREA_SEED
    ]

    return {
        "users": users,
        "userTypes": user_types,
        "roles": roles,
        "userPermissions": {
            "admin_uid": {
                "userId": "admin_uid",
                **ADMIN_PERMISSIONS,
                "updatedAt": now,
                "updatedBy": "system",
            },
            "requester_uid": {
                "userId": "requester_uid",
                **REQUEST_USER_PERMISSIONS,
                "updatedAt": now,
                "updatedBy": "system",
            },
            "approver_uid": {
                "userId": "approver_uid",
                **APPROVER_PERMISSIONS,
                "updatedAt": now,
                "updatedBy": "system",
            },
            "teamlead_uid": {
                "userId": "teamlead_uid",
                **TEAM_LEAD_PERMISSIONS,
                "updatedAt": now,
                "updatedBy": "system",
            },
            "member_uid": {
                "userId": "member_uid",
                **TEAM_MEMBER_PERMISSIONS,
                "updatedAt": now,
                "updatedBy": "system",
            },
        },
        "departments": departments,
        "systems": SYSTEM_SEED,
        "categories": categories,
        "areas": areas,
        "teams": TEAM_SEED,
        "tickets": [],
        "ticketNotes": [],
        "ticketStatusHistory": [],
        "ticketAttachments": [],
        "ticketCounters": {
            "default": {
                "lastTicketNo": 0,
                "prefix": "KG-TKT",
                "updatedAt": now,
            }
        },
        "auditLogs": [
            {
                "id": "audit_seed_admin",
                "module": "User",
                "action": "CREATE_USER",
                "recordId": "admin_uid",
                "oldValue": None,
                "newValue": {"fullName": "Admin User", "email": "admin@company.com"},
                "createdBy": "system",
                "createdByName": "System",
                "createdAt": now,
            }
        ],
    }
