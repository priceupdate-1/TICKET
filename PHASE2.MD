Below is the **Next Phase Requirement Document** for the **Ticket Module**.
Current phase completed: **Authentication + User Management + User Type + Permission**.
Now next phase: **Ticket Creation + Firebase Save + Ticket List + Ticket Detail + Authorization Flow**.

Your existing Lattice data already tracks fields like **ID, Activity, Area, Created At, Creator, Label, Priority, Status, Title, Assignee, Reporter, Verifier, Work Batch, Workspace Name**, so our ticket module should follow this structure but save everything properly in Firebase Firestore. 
For Trybe, ticket categories should support data/labour/mapping issues because the Trybe file contains employee code, attendance, pcs, cts, and amount data, and previous mapping issue data shows Trybe/labour mismatch use cases. 

---

# Phase 2 — Ticket Module Implementation

## Phase 2 Name

```text
Ticket Creation + Ticket List + Ticket Detail + Firebase Save + Authorization Flow
```

## Main Goal

Now we need to implement the ticket system after user management.

The system should allow:

```text
User creates ticket
↓
Ticket saved in Firebase Firestore
↓
Ticket status becomes Pending Authorization
↓
Authorized Person can see all pending tickets
↓
Authorized Person approves / rejects / asks for more information
↓
Approved ticket goes to Team / Management
↓
Team works on ticket and updates notes/status
```

---

# 1. Phase 2 Scope

## Include in this phase

```text
1. Ticket Create Page
2. Ticket Save in Firestore
3. My Tickets Page
4. All Tickets Page
5. Ticket Detail Page
6. Pending Authorization Page
7. Approve / Reject / Need More Information
8. Assign Team
9. Ticket Notes
10. Ticket Status History
11. Basic Ticket Dashboard Cards
12. Firebase Storage for attachments, optional in this phase
13. Audit Log for ticket actions
```

## Not included yet

Keep these for later phase:

```text
1. Gmail SMTP email
2. Advanced notification
3. SLA escalation
4. Excel export
5. Full reports
6. Advanced dashboard charts
```

---

# 2. Required Pages

Add these routes:

```text
/tickets
/tickets/create
/tickets/view/:id
/tickets/edit/:id
/tickets/my
/tickets/pending-authorization
/tickets/approved
/tickets/team
/tickets/completed
```

## Page-wise purpose

| Page                             | Purpose                                                    |
| -------------------------------- | ---------------------------------------------------------- |
| `/tickets/create`                | User creates new ticket                                    |
| `/tickets/my`                    | User sees own tickets                                      |
| `/tickets`                       | Admin / Authorized Person sees tickets based on permission |
| `/tickets/view/:id`              | Full ticket detail page                                    |
| `/tickets/edit/:id`              | Edit ticket before approval or if more info requested      |
| `/tickets/pending-authorization` | Authorized Person approval queue                           |
| `/tickets/team`                  | Team Lead / Work Team assigned tickets                     |
| `/tickets/completed`             | Completed tickets waiting for verification/closure         |

---

# 3. Ticket Creation Flow

## User creates ticket

User fills ticket form:

```text
System: Lattice / Trybe
Category: Bug / New Requirement / Change Request / Data Issue / Report Issue / Access Rights
Area: Based on selected system
Priority: Urgent / High / Medium / Low
Title
Description
Attachment, optional
Expected Date, optional
```

After submit:

```text
Save ticket in Firestore
Generate ticket number
Set status = Pending Authorization
Set createdBy = logged-in user UID
Set createdByName = logged-in user name
Set authorizedPersonId based on system/area
Create status history record
Create audit log record
```

---

# 4. Ticket Status Flow

Use this status flow in Phase 2:

```text
Draft
↓
Pending Authorization
↓
Need More Information
↓
Approved
↓
Assigned To Team
↓
In Progress
↓
Completed
↓
Closed
```

Also support:

```text
Rejected
On Hold
Reopened
Cancelled
Duplicate
```

## Status meaning

| Status                | Meaning                                  |
| --------------------- | ---------------------------------------- |
| Draft                 | Ticket saved but not submitted           |
| Pending Authorization | Waiting for authorized person            |
| Need More Information | User must update ticket details          |
| Approved              | Authorized person approved               |
| Rejected              | Authorized person rejected               |
| Assigned To Team      | Approved and assigned to team            |
| In Progress           | Team started work                        |
| On Hold               | Ticket paused                            |
| Completed             | Team completed work                      |
| Closed                | Authorized person closed ticket          |
| Reopened              | Ticket reopened after completion/closure |

---

# 5. Ticket Create Form Requirement

## Fields

```text
System
Category
Area
Priority
Title
Description
Expected Date
Attachment
Submit Button
Save Draft Button
Cancel Button
```

## Validation

```text
System is required
Category is required
Area is required
Priority is required
Title is required
Description is required
Title minimum 5 characters
Description minimum 20 characters
Attachment max size rule, if file upload added
```

## Button behavior

### Save Draft

```text
status = Draft
visible only to created user
```

### Submit Ticket

```text
status = Pending Authorization
visible to Authorized Person
```

---

# 6. Firestore Collections for Phase 2

## 6.1 `tickets`

Collection name:

```text
tickets
```

Document ID:

```text
Auto Firestore ID
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
  "description": "Detailed issue entered by user",
  "status": "Pending Authorization",

  "createdBy": "request_user_uid",
  "createdByName": "User Name",
  "createdByEmail": "user@company.com",
  "createdAt": "timestamp",

  "authorizedPersonId": "authorized_uid",
  "authorizedPersonName": "Authorized User Name",

  "approvedBy": null,
  "approvedByName": null,
  "approvedAt": null,

  "rejectedBy": null,
  "rejectedByName": null,
  "rejectedAt": null,
  "rejectionReason": null,

  "assignedTeamId": null,
  "assignedTeamName": null,
  "assignedTo": null,
  "assignedToName": null,

  "expectedDate": null,
  "dueDate": null,

  "completedBy": null,
  "completedByName": null,
  "completedAt": null,

  "closedBy": null,
  "closedByName": null,
  "closedAt": null,

  "reopenCount": 0,
  "isDeleted": false,

  "updatedAt": "timestamp",
  "updatedBy": "uid"
}
```

---

## 6.2 `ticketNotes`

Collection name:

```text
ticketNotes
```

Structure:

```json
{
  "ticketId": "ticket_doc_id",
  "ticketNo": "KG-TKT-000001",
  "noteType": "User Comment",
  "noteText": "Please check this issue urgently.",
  "visibility": "Public",
  "createdBy": "uid",
  "createdByName": "User Name",
  "createdAt": "timestamp",
  "isDeleted": false
}
```

## Note types

```text
User Comment
Approval Note
Work Note
Internal Note
Resolution Note
Rejection Note
More Information Note
Closure Note
Reopen Note
```

## Visibility

```text
Public = visible to all related users
Internal = visible only to Authorized Person / Team / Admin
```

---

## 6.3 `ticketStatusHistory`

Collection name:

```text
ticketStatusHistory
```

Structure:

```json
{
  "ticketId": "ticket_doc_id",
  "ticketNo": "KG-TKT-000001",
  "oldStatus": "Pending Authorization",
  "newStatus": "Approved",
  "changedBy": "uid",
  "changedByName": "Authorized Person Name",
  "changeNote": "Ticket approved and assigned to Lattice team.",
  "changedAt": "timestamp"
}
```

---

## 6.4 `ticketAttachments`

Collection name:

```text
ticketAttachments
```

Structure:

```json
{
  "ticketId": "ticket_doc_id",
  "ticketNo": "KG-TKT-000001",
  "fileName": "screenshot.png",
  "fileUrl": "firebase_storage_url",
  "fileType": "image/png",
  "fileSize": 123456,
  "uploadedBy": "uid",
  "uploadedByName": "User Name",
  "uploadedAt": "timestamp",
  "isDeleted": false
}
```

Storage path:

```text
ticket-attachments/{ticketId}/{fileName}
```

---

## 6.5 `ticketCounters`

Use this to generate ticket numbers.

Collection:

```text
ticketCounters
```

Document:

```text
default
```

Structure:

```json
{
  "lastTicketNo": 1,
  "prefix": "KG-TKT",
  "updatedAt": "timestamp"
}
```

Ticket number format:

```text
KG-TKT-000001
KG-TKT-000002
KG-TKT-000003
```

Important: ticket number generation should be handled using Firestore transaction to avoid duplicate ticket numbers.

---

## 6.6 `auditLogs`

Add ticket actions also:

```json
{
  "module": "Ticket",
  "action": "CREATE_TICKET",
  "recordId": "ticket_doc_id",
  "recordNo": "KG-TKT-000001",
  "oldValue": null,
  "newValue": {
    "status": "Pending Authorization",
    "title": "Ticket title"
  },
  "createdBy": "uid",
  "createdByName": "User Name",
  "createdAt": "timestamp"
}
```

Ticket audit actions:

```text
CREATE_TICKET
UPDATE_TICKET
SUBMIT_TICKET
APPROVE_TICKET
REJECT_TICKET
NEED_MORE_INFORMATION
ASSIGN_TEAM
ASSIGN_MEMBER
ADD_NOTE
UPDATE_STATUS
COMPLETE_TICKET
CLOSE_TICKET
REOPEN_TICKET
DELETE_TICKET
```

---

# 7. Master Collections Required Before Ticket Create

Before ticket create works, make sure these master collections exist.

## `systems`

```json
{
  "name": "Lattice",
  "code": "LATTICE",
  "isActive": true,
  "authorizedPersonIds": ["uid_authorized_person"]
}
```

Seed:

```text
Lattice
Trybe
```

---

## `categories`

```json
{
  "name": "Bug",
  "code": "BUG",
  "isActive": true
}
```

Seed:

```text
Bug
New Requirement
Change Request
Data Issue
Report Issue
Access Rights
Support Query
```

---

## `areas`

```json
{
  "systemId": "system_lattice",
  "systemName": "Lattice",
  "name": "Pricing",
  "code": "PRICING",
  "authorizedPersonIds": ["uid_authorized_person"],
  "defaultTeamId": "team_lattice",
  "isActive": true
}
```

Lattice areas:

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

Trybe areas:

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

## `teams`

```json
{
  "name": "Lattice Support Team",
  "systemId": "system_lattice",
  "systemName": "Lattice",
  "teamLeadId": "uid_team_lead",
  "teamLeadName": "Team Lead Name",
  "memberIds": ["uid_member_1", "uid_member_2"],
  "isActive": true
}
```

---

# 8. Permission Rules for Ticket Module

Use already implemented user permissions.

## Required permissions

```text
canCreateTicket
canViewOwnTicket
canViewAllTickets
canApproveTicket
canRejectTicket
canAssignTeam
canWorkOnTicket
canAddNotes
canCloseTicket
canReopenTicket
```

## Visibility logic

| User Type         | Ticket Visibility                                         |
| ----------------- | --------------------------------------------------------- |
| Request User      | Own tickets only                                          |
| Authorized Person | All tickets or tickets assigned to them for authorization |
| Team Lead         | Tickets assigned to their team                            |
| Work Team Member  | Tickets assigned to them                                  |
| Admin             | All tickets                                               |
| Super Admin       | All tickets                                               |

---

# 9. Ticket List Requirement

## My Tickets Page

Show tickets where:

```text
createdBy == loggedInUser.uid
```

Columns:

```text
Ticket No
System
Area
Category
Priority
Title
Status
Created Date
Updated Date
Action
```

Actions:

```text
View
Edit, only if Draft or Need More Information
Cancel, only if Draft or Pending Authorization
Reopen, only if Closed
```

---

## All Tickets Page

For Admin / Authorized Person.

Filters:

```text
System
Area
Category
Priority
Status
Created By
Assigned Team
Date Range
```

Columns:

```text
Ticket No
System
Area
Category
Priority
Title
Created By
Authorized Person
Assigned Team
Assigned To
Status
Created Date
Action
```

---

## Pending Authorization Page

Show tickets where:

```text
status == Pending Authorization
authorizedPersonId == loggedInUser.uid
```

Admin can see all.

Actions:

```text
Approve
Reject
Need More Information
View Detail
```

---

# 10. Ticket Detail Page Requirement

Ticket detail page should show:

```text
Ticket basic details
Current status
Created by details
Approval section
Assigned team section
Notes/comments
Attachments
Status history
Audit history
Action buttons based on permission
```

## Action buttons by status

| Status                | Allowed Action                         |
| --------------------- | -------------------------------------- |
| Draft                 | Edit, Submit, Delete                   |
| Pending Authorization | Approve, Reject, Need More Information |
| Need More Information | Edit, Resubmit                         |
| Approved              | Assign Team                            |
| Assigned To Team      | Start Work, Assign Member              |
| In Progress           | Add Work Note, On Hold, Complete       |
| Completed             | Close, Reopen                          |
| Closed                | Reopen                                 |

---

# 11. Approval Action Logic

## Approve Ticket

Authorized person selects:

```text
Assigned Team
Approval Note
Due Date, optional
```

System update:

```text
tickets.status = Approved
tickets.approvedBy = currentUser.uid
tickets.approvedByName = currentUser.fullName
tickets.approvedAt = current timestamp
tickets.assignedTeamId = selected team id
tickets.assignedTeamName = selected team name
```

Also create:

```text
ticketNotes record
ticketStatusHistory record
auditLogs record
```

---

## Reject Ticket

Authorized person enters:

```text
Rejection Reason
```

System update:

```text
tickets.status = Rejected
tickets.rejectedBy = currentUser.uid
tickets.rejectedByName = currentUser.fullName
tickets.rejectedAt = current timestamp
tickets.rejectionReason = reason
```

Also create:

```text
ticketNotes record with noteType = Rejection Note
ticketStatusHistory record
auditLogs record
```

---

## Need More Information

Authorized person enters:

```text
Required information note
```

System update:

```text
tickets.status = Need More Information
```

User can edit and resubmit.

---

# 12. Team Work Logic

## Assign Team Member

Team Lead selects member.

System update:

```text
tickets.status = Assigned To Team
tickets.assignedTo = selected member uid
tickets.assignedToName = selected member name
```

## Start Work

Team member clicks Start Work.

System update:

```text
tickets.status = In Progress
```

## Add Work Note

Team member adds note.

Save in:

```text
ticketNotes
```

## Complete Ticket

Team member enters:

```text
Resolution Note
```

System update:

```text
tickets.status = Completed
tickets.completedBy = currentUser.uid
tickets.completedByName = currentUser.fullName
tickets.completedAt = current timestamp
```

---

# 13. Firebase Service Functions

Create service file:

```text
src/services/ticketService.js
```

Required functions:

```text
createTicket(ticketData)
getMyTickets(userId)
getAllTickets(filters)
getTicketById(ticketId)
updateTicket(ticketId, updateData)
submitTicket(ticketId)
approveTicket(ticketId, approvalData)
rejectTicket(ticketId, rejectionReason)
requestMoreInfo(ticketId, note)
assignTeam(ticketId, teamData)
assignMember(ticketId, memberData)
startWork(ticketId)
addTicketNote(ticketId, noteData)
completeTicket(ticketId, resolutionNote)
closeTicket(ticketId, closureNote)
reopenTicket(ticketId, reopenReason)
uploadTicketAttachment(ticketId, file)
getTicketStatusHistory(ticketId)
getTicketNotes(ticketId)
```

---

# 14. Firestore Save Logic

When creating a ticket, do this in one transaction/batch:

```text
1. Read ticketCounters/default
2. Increment lastTicketNo
3. Generate ticketNo
4. Create ticket document
5. Create ticketStatusHistory document
6. Create auditLogs document
7. Commit batch/transaction
```

Pseudo logic:

```text
createTicket()
  validate form
  get current user
  get selected system/category/area
  find authorized person from area or system
  generate ticket number using transaction
  save ticket in tickets collection
  save status history
  save audit log
  redirect to ticket detail page
```

---

# 15. Basic Dashboard Cards for Phase 2

Add simple cards only, no chart required yet.

For Request User:

```text
My Total Tickets
My Pending Tickets
My Approved Tickets
My Completed Tickets
My Closed Tickets
```

For Authorized Person:

```text
Pending Authorization
Approved Today
Rejected Today
Need More Information
Completed Waiting Closure
```

For Team Lead / Team Member:

```text
Assigned To My Team
Assigned To Me
In Progress
Completed
On Hold
```

For Admin:

```text
Total Tickets
Pending Authorization
Approved
In Progress
Completed
Closed
Rejected
```

---

# 16. Phase 2 Development Order

Follow this exact order.

```text
1. Create ticket master collections: systems, categories, areas, teams
2. Seed systems: Lattice, Trybe
3. Seed categories
4. Seed Lattice and Trybe areas
5. Create ticketCounters/default
6. Create ticketService.js
7. Build Ticket Create Page
8. Save ticket in Firestore
9. Create My Tickets Page
10. Create All Tickets Page
11. Create Ticket Detail Page
12. Create ticketNotes section
13. Create ticketStatusHistory section
14. Create Pending Authorization Page
15. Add Approve action
16. Add Reject action
17. Add Need More Information action
18. Add Assign Team action
19. Add Team Ticket Page
20. Add Start Work action
21. Add Work Note action
22. Add Complete Ticket action
23. Add Close Ticket action
24. Add Reopen Ticket action
25. Add audit log for all ticket actions
26. Test full ticket flow
```

---

# 17. Phase 2 Acceptance Criteria

Phase 2 is complete only when:

```text
User can create ticket
Ticket saves in Firebase Firestore
Ticket number generates automatically
Ticket status becomes Pending Authorization
My Tickets page shows created tickets
Authorized Person can see pending tickets
Authorized Person can approve ticket
Authorized Person can reject ticket
Authorized Person can ask for more information
Approved ticket can be assigned to team
Team can see assigned ticket
Team member can start work
Team member can add work note
Team member can mark ticket completed
Authorized person can close ticket
Ticket notes save in Firestore
Ticket status history saves in Firestore
Audit log saves for ticket actions
Permission-based access works
```

---

# Final Developer Instruction

Now implement **Phase 2 — Ticket Module**. User management is already completed, so use existing logged-in user data, user type, role, and permission system. Create the ticket form and save all ticket data in Firebase Firestore. Every ticket must have a unique ticket number, system, category, area, priority, title, description, status, created user, authorized person, timestamps, notes, and status history. After ticket creation, the default status should be **Pending Authorization**. Authorized Person should be able to approve, reject, or ask for more information. After approval, ticket should be assigned to the team and then worked by the team member.
