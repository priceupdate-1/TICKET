PERMISSIONS = [
    ("canCreateTicket", "Can Create Ticket"),
    ("canViewOwnTicket", "Can View Own Ticket"),
    ("canViewAllTickets", "Can View All Tickets"),
    ("canApproveTicket", "Can Approve Ticket"),
    ("canRejectTicket", "Can Reject Ticket"),
    ("canAssignTeam", "Can Assign Team"),
    ("canWorkOnTicket", "Can Work On Ticket"),
    ("canAddNotes", "Can Add Notes"),
    ("canCloseTicket", "Can Close Ticket"),
    ("canReopenTicket", "Can Reopen Ticket"),
    ("canManageUsers", "Can Manage Users"),
    ("canManageMasters", "Can Manage Masters"),
    ("canManageSMTP", "Can Manage SMTP"),
    ("canViewReports", "Can View Reports"),
]

SYSTEM_ACCESS = ["Lattice", "Trybe"]

DEFAULT_DASHBOARDS = ["admin", "requester", "approver", "team", "viewer"]

TICKET_STATUSES = [
    "Draft",
    "Pending Authorization",
    "Need More Information",
    "Approved",
    "Rejected",
    "Assigned To Team",
    "In Progress",
    "On Hold",
    "Completed",
    "Closed",
    "Reopened",
    "Cancelled",
    "Duplicate",
]

TICKET_PRIORITIES = ["Urgent", "High", "Medium", "Low"]

NOTE_TYPES = [
    "User Comment",
    "Approval Note",
    "Work Note",
    "Internal Note",
    "Resolution Note",
    "Rejection Note",
    "More Information Note",
    "Closure Note",
    "Reopen Note",
]

NOTE_VISIBILITIES = ["Public", "Internal"]

USER_TYPE_SEED = [
    ("ut_super_admin", "Super Admin", "SUPER_ADMIN", "Full access to all modules", 1),
    ("ut_admin", "Admin", "ADMIN", "User management, masters, settings", 2),
    ("ut_request_user", "Request User", "REQUEST_USER", "Creates and tracks own tickets", 3),
    ("ut_authorized_person", "Authorized Person", "AUTHORIZED_PERSON", "Approves or rejects tickets", 4),
    ("ut_team_lead", "Management / Team Lead", "TEAM_LEAD", "Assigns and monitors work", 5),
    ("ut_team_member", "Work Team Member", "TEAM_MEMBER", "Works assigned tickets", 6),
    ("ut_viewer", "Viewer", "VIEWER", "Read-only access", 7),
]

ROLE_SEED = [
    ("role_super_admin", "Super Admin", "SUPER_ADMIN", "Full system role"),
    ("role_admin", "Admin", "ADMIN", "Administrative user role"),
    ("role_requester", "Requester", "REQUESTER", "Request user role"),
    ("role_approver", "Approver", "APPROVER", "Authorization role"),
    ("role_team_lead", "Team Lead", "TEAM_LEAD", "Team management role"),
    ("role_team_member", "Team Member", "TEAM_MEMBER", "Execution role"),
    ("role_viewer", "Viewer", "VIEWER", "Read-only role"),
]

DEPARTMENT_SEED = [
    ("dept_it", "IT", "IT"),
    ("dept_sales", "Sales", "SALES"),
    ("dept_manufacturing", "Manufacturing", "MFG"),
    ("dept_labour", "Labour", "LABOUR"),
    ("dept_hr", "HR", "HR"),
    ("dept_accounts", "Accounts", "ACCOUNTS"),
    ("dept_management", "Management", "MGMT"),
    ("dept_data", "Data Team", "DATA"),
]

SYSTEM_SEED = [
    {
        "id": "system_lattice",
        "name": "Lattice",
        "code": "LATTICE",
        "isActive": True,
        "authorizedPersonIds": ["approver_uid"],
    },
    {
        "id": "system_trybe",
        "name": "Trybe",
        "code": "TRYBE",
        "isActive": True,
        "authorizedPersonIds": ["approver_uid"],
    },
]

CATEGORY_SEED = [
    ("cat_bug", "Bug", "BUG"),
    ("cat_new_requirement", "New Requirement", "NEW_REQUIREMENT"),
    ("cat_change_request", "Change Request", "CHANGE_REQUEST"),
    ("cat_data_issue", "Data Issue", "DATA_ISSUE"),
    ("cat_report_issue", "Report Issue", "REPORT_ISSUE"),
    ("cat_access_rights", "Access Rights", "ACCESS_RIGHTS"),
    ("cat_support_query", "Support Query", "SUPPORT_QUERY"),
]

AREA_SEED = [
    ("area_lattice_pricing", "system_lattice", "Lattice", "Pricing", "PRICING", "team_lattice"),
    ("area_lattice_inventory", "system_lattice", "Lattice", "Inventory", "INVENTORY", "team_lattice"),
    ("area_lattice_sales", "system_lattice", "Lattice", "Sales", "SALES", "team_lattice"),
    ("area_lattice_report", "system_lattice", "Lattice", "Report", "REPORT", "team_lattice"),
    ("area_lattice_lab_result", "system_lattice", "Lattice", "Lab Result", "LAB_RESULT", "team_lattice"),
    ("area_lattice_recut", "system_lattice", "Lattice", "Recut", "RECUT", "team_lattice"),
    ("area_lattice_purchase_to_single", "system_lattice", "Lattice", "Purchase To Single", "PURCHASE_TO_SINGLE", "team_lattice"),
    ("area_lattice_mix_to_single", "system_lattice", "Lattice", "Mix To Single", "MIX_TO_SINGLE", "team_lattice"),
    ("area_lattice_user_rights", "system_lattice", "Lattice", "User Rights", "USER_RIGHTS", "team_lattice"),
    ("area_lattice_api", "system_lattice", "Lattice", "API", "API", "team_lattice"),
    ("area_lattice_dna_page", "system_lattice", "Lattice", "DNA Page", "DNA_PAGE", "team_lattice"),
    ("area_trybe_labour", "system_trybe", "Trybe", "Labour", "LABOUR", "team_trybe"),
    ("area_trybe_employee_mapping", "system_trybe", "Trybe", "Employee Mapping", "EMPLOYEE_MAPPING", "team_trybe"),
    ("area_trybe_attendance", "system_trybe", "Trybe", "Attendance", "ATTENDANCE", "team_trybe"),
    ("area_trybe_production", "system_trybe", "Trybe", "Production", "PRODUCTION", "team_trybe"),
    ("area_trybe_payroll", "system_trybe", "Trybe", "Payroll", "PAYROLL", "team_trybe"),
    ("area_trybe_report", "system_trybe", "Trybe", "Report", "REPORT", "team_trybe"),
    ("area_trybe_monthly_process", "system_trybe", "Trybe", "Monthly Process", "MONTHLY_PROCESS", "team_trybe"),
    ("area_trybe_data_import", "system_trybe", "Trybe", "Data Import", "DATA_IMPORT", "team_trybe"),
]

TEAM_SEED = [
    {
        "id": "team_lattice",
        "name": "Lattice Support Team",
        "systemId": "system_lattice",
        "systemName": "Lattice",
        "teamLeadId": "teamlead_uid",
        "teamLeadName": "Team Lead User",
        "memberIds": ["member_uid"],
        "isActive": True,
    },
    {
        "id": "team_trybe",
        "name": "Trybe Data Team",
        "systemId": "system_trybe",
        "systemName": "Trybe",
        "teamLeadId": "teamlead_uid",
        "teamLeadName": "Team Lead User",
        "memberIds": ["member_uid"],
        "isActive": True,
    },
]

ADMIN_PERMISSIONS = {key: True for key, _ in PERMISSIONS}

REQUEST_USER_PERMISSIONS = {
    "canCreateTicket": True,
    "canViewOwnTicket": True,
    "canAddNotes": True,
    "canReopenTicket": True,
}

VIEWER_PERMISSIONS = {
    "canViewOwnTicket": True,
    "canViewReports": True,
}

APPROVER_PERMISSIONS = {
    "canCreateTicket": True,
    "canViewOwnTicket": True,
    "canViewAllTickets": True,
    "canApproveTicket": True,
    "canRejectTicket": True,
    "canAssignTeam": True,
    "canAddNotes": True,
    "canCloseTicket": True,
    "canReopenTicket": True,
}

TEAM_LEAD_PERMISSIONS = {
    "canCreateTicket": True,
    "canViewOwnTicket": True,
    "canAssignTeam": True,
    "canWorkOnTicket": True,
    "canAddNotes": True,
    "canReopenTicket": True,
}

TEAM_MEMBER_PERMISSIONS = {
    "canCreateTicket": True,
    "canViewOwnTicket": True,
    "canWorkOnTicket": True,
    "canAddNotes": True,
}
