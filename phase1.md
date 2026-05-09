Below is the **proper requirement document + Firebase Firestore collection plan + phase-wise implementation instruction** for your internal ticket management system.

This is written like a developer handover document.

---

# Internal Ticket Management System — Requirement Document

## 1. Project Overview

We need to convert the current basic one-page ticket system into a proper internal ticket management application.

The system will manage tickets for internal company systems such as:

```text
1. Lattice
2. Trybe
```

The current Lattice export already contains ticket/task fields like **ID, Activity, Area, Label, Priority, Status, Title, Assignee, Creator, Reporter, Verifier, Work Batch, Workspace Name**, and statuses such as **Open, Release, Completed, Closed, Later, To Do**. So the new system should keep this type of structure but add proper authentication, approval, user rights, team workflow, notes, notification, and Firebase database structure. 

For Trybe, the system should also support labour/data-related issues because the Trybe file contains employee/labour data and mapping issues such as employee code mismatches and missing Trybe transactions. 

---

# 2. Main Business Flow

The required ticket flow is simple:

```text
User creates ticket
        ↓
Authorized Person sees all new tickets
        ↓
Authorized Person approves / rejects / asks for more information
        ↓
If approved, ticket goes to Management / Work Team
        ↓
Team works on the ticket
        ↓
Team adds updates, notes, attachments, and status changes
        ↓
Team marks ticket as completed
        ↓
Authorized Person verifies
        ↓
Ticket is closed
        ↓
If issue still exists, ticket can be reopened
```

---

# 3. Main User Types

Implement these user types first:

| User Type              | Purpose                                           |
| ---------------------- | ------------------------------------------------- |
| Super Admin            | Full access to all modules                        |
| Admin                  | User management, masters, settings                |
| Request User           | Creates ticket and tracks own tickets             |
| Authorized Person      | Views all tickets, approves/rejects, assigns team |
| Management / Team Lead | Receives approved tickets and assigns work        |
| Work Team Member       | Works on assigned tickets and updates notes       |
| Viewer                 | Read-only access, optional                        |

---

# 4. System Modules

The final application should have these modules:

```text
1. Authentication
2. User CRUD
3. User Type & Role Permission
4. System Master: Lattice / Trybe
5. Category Master
6. Area / Module Master
7. Team Master
8. Ticket Creation
9. Ticket Authorization
10. Team Work Dashboard
11. Notes & Comments
12. Attachments
13. Status History
14. Notification
15. Gmail SMTP Email
16. Dashboard
17. Reports
18. Audit Log
```

---

# 5. Phase-Wise Implementation Plan

## Phase 1 — Main Foundation

This is the first phase you should work on now.

### Phase 1 Name

```text
Authentication + User CRUD + Role Permission + Firebase Base Setup
```

### Phase 1 Goal

Currently the system is basic and one-page. In Phase 1, convert it into a proper application with:

```text
Login
Logout
Protected Routes
Main Layout
Sidebar Menu
User CRUD
User Type
Role
Permission
Profile Page
Firebase Firestore Structure
Audit Log
```

### Phase 1 Not Included

Do not start these until Phase 1 is completed:

```text
Ticket creation
Ticket approval
Team assignment
SMTP email
Notification
Dashboard charts
Reports
Attachment upload
```

Reason: first we need proper user authentication, access control, and user management.

---

## Phase 2 — Master Setup

After Phase 1, implement master data.

```text
System Master
Category Master
Area Master
Priority Master
Status Master
Team Master
Authorized Person Mapping
```

Example:

```text
System: Lattice
Areas: Pricing, Inventory, Report, Lab Result, Sales, Recut

System: Trybe
Areas: Labour, Employee Mapping, Attendance, Production, Payroll, Report
```

---

## Phase 3 — Ticket Creation

Implement ticket create/list/detail.

```text
Create Ticket
My Tickets
All Tickets
Ticket Detail Page
Ticket Status
Ticket Priority
Ticket Category
Ticket Area
Ticket Attachments
Ticket Basic Comments
```

Default ticket status after submit:

```text
Pending Authorization
```

---

## Phase 4 — Authorization Flow

Implement approval flow.

```text
Authorized Person Dashboard
Pending Authorization Tickets
Approve Ticket
Reject Ticket
Need More Information
Assign Team
Change Priority
Add Approval Note
```

After approval:

```text
Status = Approved
Assigned Team = selected team
Ticket visible to Team Lead
```

---

## Phase 5 — Team Work Flow

Implement management/team workflow.

```text
Team Dashboard
Assigned Tickets
Assign Team Member
Start Work
In Progress
Add Work Note
Internal Note
Upload File
Mark Completed
```

---

## Phase 6 — Verification, Close, Reopen

Implement final lifecycle.

```text
Completed Tickets
Authorized Person Verification
Close Ticket
Reopen Ticket
Reopen Reason
Reopen Count
Closure Note
Resolution Note
```

---

## Phase 7 — Notification + Gmail SMTP

Implement notification after workflow is stable.

```text
In-app notification
Email notification
Gmail SMTP
Email queue
Email templates
SMTP settings page
Test mail
```

Important instruction:

```text
Do not expose Gmail SMTP password in frontend.
SMTP should be handled through backend / Firebase Cloud Functions / secure server.
```

---

## Phase 8 — Dashboard + Reports

Implement management reporting.

```text
Open Tickets
Closed Tickets
Pending Authorization
Urgent Tickets
Team-wise Tickets
User-wise Tickets
Reopened Tickets
Delayed Tickets
Export to Excel
```

---

# 6. Phase 1 Detailed Requirement

## 6.1 Authentication

### Login Page

Route:

```text
/login
```

Fields:

```text
Email
Password
Login Button
Forgot Password
```

Validation:

```text
Email required
Password required
Invalid email format
Invalid login message
Inactive user cannot login
Deleted user cannot login
```

Login flow:

```text
User enters email/password
        ↓
Firebase Authentication validates credentials
        ↓
System checks users collection in Firestore
        ↓
Check isActive = true
        ↓
Check isDeleted = false
        ↓
Load userType, role, permissions
        ↓
Redirect to dashboard
```

---

## 6.2 Logout

Logout should:

```text
Clear Firebase auth session
Clear local user state
Redirect to /login
```

---

## 6.3 Protected Routes

Create route guard.

Rules:

```text
Without login, user cannot access application pages.
Without permission, user cannot access restricted pages.
Unauthorized access redirects to /unauthorized.
```

Routes for Phase 1:

```text
/login
/dashboard
/users
/users/add
/users/edit/:id
/users/view/:id
/profile
/settings
/unauthorized
```

---

## 6.4 Main Layout

After login, user should see:

```text
Top Header
Left Sidebar
Main Content Area
Profile Dropdown
Logout Button
Notification Bell Placeholder
```

Sidebar should be permission based.

Example for Admin:

```text
Dashboard
Users
User Types
Roles
Permissions
Profile
Settings
```

Example for Request User:

```text
Dashboard
My Tickets
Create Ticket
Profile
```

In Phase 1, ticket menu can show as disabled or hidden until Phase 3.

---

# 7. User CRUD Requirement

## 7.1 User List Page

Route:

```text
/users
```

Columns:

```text
Employee Code
Full Name
Email
Mobile No.
Department
Designation
User Type
Role
System Access
Active / Inactive
Created Date
Action
```

Actions:

```text
View
Edit
Activate / Deactivate
Reset Password
Soft Delete
```

---

## 7.2 Add User Page

Route:

```text
/users/add
```

Sections:

### Basic Details

```text
Employee Code
Full Name
Email
Mobile No.
Department
Designation
Reporting Manager
```

### Access Details

```text
User Type
Role
System Access: Lattice / Trybe / Both
Default Dashboard
Active / Inactive
```

### Permission Details

```text
Can Create Ticket
Can View Own Ticket
Can View All Tickets
Can Approve Ticket
Can Reject Ticket
Can Assign Team
Can Work On Ticket
Can Add Notes
Can Close Ticket
Can Reopen Ticket
Can Manage Users
Can Manage Masters
Can Manage SMTP
Can View Reports
```

### Notification Preference

```text
Email Notification: Yes / No
In-App Notification: Yes / No
```

---

## 7.3 Edit User Page

Route:

```text
/users/edit/:id
```

Admin can edit:

```text
Full Name
Mobile No.
Department
Designation
Reporting Manager
User Type
Role
System Access
Permissions
Active / Inactive
Notification Preference
```

Admin should not directly edit email after user creation unless required.

---

## 7.4 View User Page

Route:

```text
/users/view/:id
```

Display:

```text
Basic user details
Access details
Permission details
Created by
Created date
Updated by
Updated date
Status
```

---

## 7.5 Soft Delete

Do not permanently delete user.

When deleting:

```text
isDeleted = true
isActive = false
deletedAt = current timestamp
deletedBy = logged in admin user id
```

Deleted user should not appear in active user list.

---

# 8. Firestore Collection Design

Below is the recommended Firebase Firestore structure.

---

## 8.1 `users`

Collection:

```text
users
```

Document ID:

```text
Firebase Auth UID
```

Structure:

```json
{
  "uid": "firebase_auth_uid",
  "employeeCode": "KG001",
  "fullName": "User Name",
  "email": "user@company.com",
  "mobileNo": "9999999999",
  "departmentId": "dept_it",
  "designation": "Developer",
  "reportingManagerId": "manager_uid",
  "userTypeId": "ut_admin",
  "roleId": "role_admin",
  "systemAccess": ["Lattice", "Trybe"],
  "defaultDashboard": "admin",
  "isActive": true,
  "isDeleted": false,
  "notificationEmail": true,
  "notificationInApp": true,
  "createdAt": "timestamp",
  "createdBy": "admin_uid",
  "updatedAt": "timestamp",
  "updatedBy": "admin_uid",
  "deletedAt": null,
  "deletedBy": null
}
```

---

## 8.2 `userTypes`

Collection:

```text
userTypes
```

Structure:

```json
{
  "name": "Authorized Person",
  "code": "AUTHORIZED_PERSON",
  "description": "Can view all tickets and approve/reject tickets",
  "isActive": true,
  "sortOrder": 4,
  "createdAt": "timestamp",
  "createdBy": "admin_uid"
}
```

Seed data:

```text
SUPER_ADMIN
ADMIN
REQUEST_USER
AUTHORIZED_PERSON
TEAM_LEAD
TEAM_MEMBER
VIEWER
```

---

## 8.3 `roles`

Collection:

```text
roles
```

Structure:

```json
{
  "name": "Approver",
  "code": "APPROVER",
  "description": "User can approve or reject tickets",
  "isActive": true,
  "createdAt": "timestamp",
  "createdBy": "admin_uid"
}
```

Seed data:

```text
SUPER_ADMIN
ADMIN
REQUESTER
APPROVER
TEAM_LEAD
TEAM_MEMBER
VIEWER
```

---

## 8.4 `userPermissions`

Collection:

```text
userPermissions
```

Document ID:

```text
user uid
```

Structure:

```json
{
  "userId": "firebase_auth_uid",
  "canCreateTicket": true,
  "canViewOwnTicket": true,
  "canViewAllTickets": false,
  "canApproveTicket": false,
  "canRejectTicket": false,
  "canAssignTeam": false,
  "canWorkOnTicket": false,
  "canAddNotes": true,
  "canCloseTicket": false,
  "canReopenTicket": true,
  "canManageUsers": false,
  "canManageMasters": false,
  "canManageSMTP": false,
  "canViewReports": false,
  "updatedAt": "timestamp",
  "updatedBy": "admin_uid"
}
```

---

## 8.5 `departments`

Collection:

```text
departments
```

Structure:

```json
{
  "name": "IT",
  "code": "IT",
  "isActive": true,
  "createdAt": "timestamp",
  "createdBy": "admin_uid"
}
```

Example departments:

```text
IT
Sales
Manufacturing
Labour
HR
Accounts
Management
Data Team
```

---

## 8.6 `systems`

Collection:

```text
systems
```

Structure:

```json
{
  "name": "Lattice",
  "code": "LATTICE",
  "description": "Internal Lattice system tickets",
  "authorizedPersonIds": ["uid_1"],
  "isActive": true,
  "createdAt": "timestamp",
  "createdBy": "admin_uid"
}
```

Seed data:

```text
Lattice
Trybe
```

---

## 8.7 `categories`

Collection:

```text
categories
```

Structure:

```json
{
  "name": "Bug",
  "code": "BUG",
  "description": "System issue or error",
  "isActive": true,
  "createdAt": "timestamp"
}
```

Seed data:

```text
Bug
New Requirement
Change Request
Data Issue
Access Rights
Report Issue
Integration Issue
Support Query
```

---

## 8.8 `areas`

Collection:

```text
areas
```

Structure:

```json
{
  "systemId": "system_lattice",
  "name": "Pricing",
  "code": "PRICING",
  "authorizedPersonIds": ["uid_1"],
  "defaultTeamId": "team_lattice",
  "isActive": true,
  "createdAt": "timestamp"
}
```

Example Lattice areas:

```text
Pricing
Inventory
Sales
Report
Lab Result
Recut
Purchase To Single
Mix To Single
User Rights
API
DNA Page
```

Example Trybe areas:

```text
Labour
Employee Mapping
Attendance
Production
Payroll
Report
Monthly Process
Data Import
```

---

## 8.9 `teams`

Collection:

```text
teams
```

Structure:

```json
{
  "name": "Lattice Support Team",
  "systemId": "system_lattice",
  "teamLeadId": "uid_team_lead",
  "memberIds": ["uid_1", "uid_2"],
  "isActive": true,
  "createdAt": "timestamp"
}
```

---

## 8.10 `tickets`

This will be used from Phase 3.

Collection:

```text
tickets
```

Structure:

```json
{
  "ticketNo": "KG-TKT-000001",
  "systemId": "system_lattice",
  "systemName": "Lattice",
  "categoryId": "cat_bug",
  "categoryName": "Bug",
  "areaId": "area_pricing",
  "areaName": "Pricing",
  "priority": "Urgent",
  "title": "Stone Transfer to Sales Failed",
  "description": "Issue details entered by user",
  "status": "Pending Authorization",
  "createdBy": "request_user_uid",
  "createdByName": "User Name",
  "authorizedPersonId": "authorized_uid",
  "approvedBy": null,
  "approvedAt": null,
  "rejectedBy": null,
  "rejectedAt": null,
  "rejectionReason": null,
  "assignedTeamId": null,
  "assignedTeamName": null,
  "assignedTo": null,
  "dueDate": null,
  "completedBy": null,
  "completedAt": null,
  "closedBy": null,
  "closedAt": null,
  "reopenCount": 0,
  "isDeleted": false,
  "createdAt": "timestamp",
  "updatedAt": "timestamp",
  "updatedBy": "uid"
}
```

---

## 8.11 `ticketNotes`

Collection:

```text
ticketNotes
```

Structure:

```json
{
  "ticketId": "ticket_doc_id",
  "noteType": "Work Note",
  "noteText": "Checked issue and started correction.",
  "visibility": "Public",
  "createdBy": "uid",
  "createdByName": "User Name",
  "createdAt": "timestamp"
}
```

Note types:

```text
User Comment
Approval Note
Work Note
Internal Note
Resolution Note
Reopen Note
Closure Note
```

---

## 8.12 `ticketStatusHistory`

Collection:

```text
ticketStatusHistory
```

Structure:

```json
{
  "ticketId": "ticket_doc_id",
  "oldStatus": "Approved",
  "newStatus": "In Progress",
  "changedBy": "uid",
  "changedByName": "User Name",
  "changeNote": "Work started",
  "changedAt": "timestamp"
}
```

---

## 8.13 `notifications`

Collection:

```text
notifications
```

Structure:

```json
{
  "userId": "receiver_uid",
  "title": "New ticket pending approval",
  "message": "Ticket KG-TKT-000001 requires your approval",
  "module": "Ticket",
  "recordId": "ticket_doc_id",
  "isRead": false,
  "createdAt": "timestamp"
}
```

---

## 8.14 `emailQueue`

Collection:

```text
emailQueue
```

Structure:

```json
{
  "to": ["user@company.com"],
  "cc": [],
  "subject": "Ticket Pending Approval",
  "body": "Email body content",
  "status": "Pending",
  "retryCount": 0,
  "errorMessage": null,
  "createdAt": "timestamp",
  "sentAt": null
}
```

Email status:

```text
Pending
Sent
Failed
Retry
```

---

## 8.15 `smtpSettings`

Collection:

```text
smtpSettings
```

Document ID:

```text
default
```

Structure:

```json
{
  "provider": "Gmail",
  "smtpHost": "smtp.gmail.com",
  "smtpPort": 587,
  "encryption": "TLS",
  "senderEmail": "yourgmail@gmail.com",
  "senderName": "KG Ticket System",
  "isActive": true,
  "updatedAt": "timestamp",
  "updatedBy": "admin_uid"
}
```

Important:

```text
Do not store plain SMTP password directly in Firestore.
Use Firebase Secret Manager / Cloud Function environment variable / backend environment variable.
```

---

## 8.16 `auditLogs`

Collection:

```text
auditLogs
```

Structure:

```json
{
  "module": "User",
  "action": "CREATE_USER",
  "recordId": "uid",
  "oldValue": null,
  "newValue": {
    "fullName": "User Name",
    "email": "user@company.com"
  },
  "createdBy": "admin_uid",
  "createdByName": "Admin Name",
  "createdAt": "timestamp"
}
```

Actions to log:

```text
CREATE_USER
UPDATE_USER
DEACTIVATE_USER
ACTIVATE_USER
DELETE_USER
UPDATE_PERMISSION
CREATE_TICKET
APPROVE_TICKET
REJECT_TICKET
ASSIGN_TEAM
UPDATE_STATUS
CLOSE_TICKET
REOPEN_TICKET
```

---

# 9. Ticket Status Master

Use these statuses:

```text
Draft
Pending Authorization
Need More Information
Approved
Rejected
Assigned To Team
In Progress
On Hold
Completed
Verified
Closed
Reopened
Cancelled
Duplicate
```

Recommended flow:

```text
Draft
  ↓
Pending Authorization
  ↓
Approved
  ↓
Assigned To Team
  ↓
In Progress
  ↓
Completed
  ↓
Verified
  ↓
Closed
```

Exception flows:

```text
Pending Authorization → Rejected
Pending Authorization → Need More Information
Closed → Reopened
In Progress → On Hold
```

---

# 10. Priority Master

Use these priorities:

```text
Urgent
High
Medium
Low
```

Suggested SLA:

| Priority | SLA            |
| -------- | -------------- |
| Urgent   | Same day       |
| High     | 1 working day  |
| Medium   | 3 working days |
| Low      | 7 working days |

---

# 11. Permission Matrix

| Action           | Request User | Authorized Person | Team Lead | Team Member | Admin |
| ---------------- | -----------: | ----------------: | --------: | ----------: | ----: |
| Create Ticket    |          Yes |               Yes |       Yes |         Yes |   Yes |
| View Own Ticket  |          Yes |               Yes |       Yes |         Yes |   Yes |
| View All Tickets |           No |               Yes | Team-wise |          No |   Yes |
| Approve Ticket   |           No |               Yes |        No |          No |   Yes |
| Reject Ticket    |           No |               Yes |        No |          No |   Yes |
| Assign Team      |           No |               Yes |       Yes |          No |   Yes |
| Assign Member    |           No |                No |       Yes |          No |   Yes |
| Add Notes        |          Yes |               Yes |       Yes |         Yes |   Yes |
| Work on Ticket   |           No |                No |       Yes |         Yes |   Yes |
| Complete Ticket  |           No |                No |       Yes |         Yes |   Yes |
| Close Ticket     |           No |               Yes |  Optional |          No |   Yes |
| Reopen Ticket    |          Yes |               Yes |       Yes |    Optional |   Yes |
| Manage Users     |           No |                No |        No |          No |   Yes |
| Manage Masters   |           No |                No |        No |          No |   Yes |
| Manage SMTP      |           No |                No |        No |          No |   Yes |

---

# 12. Firebase Setup Instructions

## Step 1: Create Firebase Project

Create project:

```text
KG Internal Ticket Management System
```

Enable:

```text
Firebase Authentication
Firestore Database
Firebase Storage
Cloud Functions
```

---

## Step 2: Authentication Setup

Enable provider:

```text
Email / Password
```

Later optional:

```text
Google Login
```

---

## Step 3: Firestore Database

Create Firestore in production mode.

Start with these collections:

```text
users
userTypes
roles
userPermissions
departments
auditLogs
```

Later add:

```text
systems
categories
areas
teams
tickets
ticketNotes
ticketStatusHistory
notifications
emailQueue
smtpSettings
```

---

## Step 4: Firebase Storage

Use later for attachments:

```text
ticket-attachments/{ticketId}/{fileName}
profile-images/{userId}/{fileName}
```

---

## Step 5: Cloud Functions

Use later for:

```text
Sending Gmail SMTP email
Processing emailQueue
Ticket notification triggers
Ticket number generation
```

---

# 13. Phase 1 Task Breakdown

## Task 1 — Project Structure

Create proper folder structure.

Example:

```text
src/
  components/
  layouts/
  pages/
    auth/
    dashboard/
    users/
    profile/
    settings/
  services/
    firebase/
    authService.js
    userService.js
    permissionService.js
  routes/
  utils/
  constants/
```

Acceptance:

```text
Project has clean structure.
Pages are not kept in one file.
Reusable services are created.
```

---

## Task 2 — Firebase Config

Create Firebase config file.

Required:

```text
firebaseConfig
auth
firestore db
storage
```

Acceptance:

```text
App connects with Firebase.
Firestore read/write test works.
Firebase Auth test works.
```

---

## Task 3 — Login Page

Implement:

```text
Email/password login
Validation
Error message
Loading state
Redirect after login
```

Acceptance:

```text
Valid user can login.
Invalid user gets error.
Inactive user cannot login.
Deleted user cannot login.
```

---

## Task 4 — Auth Context / Global User State

Create global login state.

Store:

```text
uid
fullName
email
userType
role
permissions
systemAccess
isActive
```

Acceptance:

```text
Logged-in user data is available across app.
Reload page keeps session.
Logout clears session.
```

---

## Task 5 — Protected Routes

Implement route protection.

Acceptance:

```text
User cannot access dashboard without login.
User cannot access users page without canManageUsers permission.
Unauthorized users redirect to /unauthorized.
```

---

## Task 6 — Main Layout

Implement:

```text
Header
Sidebar
Content area
Profile dropdown
Logout
Notification icon placeholder
```

Acceptance:

```text
Layout applies after login.
Sidebar menu changes based on permission.
```

---

## Task 7 — Seed User Types and Roles

Create default records.

User Types:

```text
Super Admin
Admin
Request User
Authorized Person
Management / Team Lead
Work Team Member
Viewer
```

Roles:

```text
Super Admin
Admin
Requester
Approver
Team Lead
Team Member
Viewer
```

Acceptance:

```text
User type dropdown loads from Firestore.
Role dropdown loads from Firestore.
```

---

## Task 8 — User CRUD

Implement:

```text
User List
Add User
Edit User
View User
Activate / Deactivate
Soft Delete
Reset Password
```

Acceptance:

```text
Admin can create user.
Admin can edit user.
Admin can deactivate user.
Admin can soft delete user.
Admin can view user detail.
```

---

## Task 9 — Permission Assignment

Implement permission checkboxes.

Acceptance:

```text
Admin can assign permissions.
Permissions are saved in userPermissions collection.
Menu changes based on permissions.
Restricted page is blocked.
```

---

## Task 10 — Profile Page

Implement logged-in user profile.

User can update:

```text
Mobile No.
Notification preference
Password
```

User cannot update:

```text
Role
User Type
Permissions
System Access
```

Acceptance:

```text
User can see own profile.
Only admin can change access details.
```

---

## Task 11 — Audit Log

Log:

```text
User created
User updated
User activated
User deactivated
User deleted
Permission changed
```

Acceptance:

```text
Every user management action creates auditLogs record.
```

---

# 14. Phase 1 Completion Criteria

Phase 1 is complete only when this is ready:

```text
Firebase project connected
Login working
Logout working
Protected routes working
Main layout ready
Sidebar permission based
User Type master ready
Role master ready
User CRUD ready
Permission assignment ready
Profile page ready
Audit log ready
Admin user ready
```

---

# 15. Development Order

Follow this exact order:

```text
1. Setup Firebase project
2. Setup Firestore
3. Setup Firebase Auth
4. Create project structure
5. Create login page
6. Create auth context/global user state
7. Create protected route
8. Create main layout
9. Seed user types
10. Seed roles
11. Create users collection
12. Create first admin user
13. Build User List
14. Build Add User
15. Build Edit User
16. Build View User
17. Build Activate/Deactivate
18. Build Soft Delete
19. Build Permission Assignment
20. Apply sidebar/page permission
21. Build Profile Page
22. Build Audit Log
23. Test full Phase 1
```

---

# 16. Final Requirement Statement for Developer

Implement Phase 1 of the internal ticket management system. The current application is basic and one-page, so convert it into a proper Firebase-based application with authentication, protected routes, layout, user management, user type, role, permissions, profile, and audit logging.

Use Firebase Authentication for login and Firestore as the main database. Admin should be able to create, edit, view, activate/deactivate, soft delete users, and assign permissions. Every user should have user type, role, system access, and permission flags. Menu and page access must work based on permissions. Ticket workflow, approval, team assignment, SMTP mail, notifications, dashboard, and reports will be implemented in later phases after this base is completed.
