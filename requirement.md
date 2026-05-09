Yes, now we will make the ticket flow **simple and proper**:

> **User creates ticket → Authorized person sees all tickets → Authorized person approves/rejects → Approved ticket goes to Management/Work Team → Team works and updates notes/status → Ticket completed/closed.**

Your current Lattice export already has useful fields like **Area, Creator, Label, Priority, Status, Title, Assignee, Reporter, Verifier, Work Batch, Workspace Name**, so we should keep that structure and add the missing approval/work-team flow on top. 
For Trybe, ticket category should also support mapping/data issues because your Trybe file shows employee mapping mismatch issues such as “Found in Trybe file, not found in Labour employee mapping” and “Found in Labour file, no Trybe transaction.” 

---

# Final Simple Ticket Flow

```text
1. User creates ticket
2. Ticket goes to Authorized Person
3. Authorized Person checks all details
4. Authorized Person approves / rejects / asks for correction
5. If approved, ticket shows to Management Team / Work Team
6. Team accepts and starts work
7. Team updates status, notes, attachment, progress
8. Work completed
9. Authorized Person or requester verifies
10. Ticket closed
11. If issue still exists, ticket reopened
```

---

# 1. User Types for This Simple Flow

For now, implement only these user types.

| User Type              | Purpose                                             |
| ---------------------- | --------------------------------------------------- |
| Request User           | Creates ticket                                      |
| Authorized Person      | Sees all tickets and approves/rejects               |
| Management / Team Lead | Receives approved tickets and assigns/monitors work |
| Work Team Member       | Works on ticket and adds updates/notes              |
| Admin                  | Manages users, categories, areas, mail, settings    |
| Super Admin            | Full access                                         |

This is better than making too many roles in the first version.

---

# 2. Main Ticket Status Flow

Use this status flow in the system.

```text
Draft
↓
Submitted
↓
Pending Authorization
↓
Approved
↓
Assigned to Team
↓
In Progress
↓
Work Updated
↓
Completed
↓
Verified
↓
Closed
```

Extra statuses:

```text
Rejected
Need More Information
On Hold
Reopened
Cancelled
Duplicate
```

---

# 3. Proper Flow With Responsibility

## Step 1: User Creates Ticket

User fills:

| Field         | Example                                             |
| ------------- | --------------------------------------------------- |
| System        | Lattice / Trybe                                     |
| Area          | Pricing, Labour, Report, Mapping, etc.              |
| Category      | Bug / New Requirement / Data Issue / Change Request |
| Priority      | Urgent / High / Medium / Low                        |
| Title         | Short issue name                                    |
| Description   | Full issue details                                  |
| Attachment    | Screenshot, Excel, PDF                              |
| Expected Date | Optional                                            |
| Created By    | Auto from login                                     |

After submit:

```text
Status = Submitted / Pending Authorization
Ticket visible to Authorized Person
Email + notification sent to Authorized Person
```

---

## Step 2: Authorized Person Reviews Ticket

Authorized person can see **all submitted tickets**.

They can do:

| Action                 | Result                                |
| ---------------------- | ------------------------------------- |
| Approve                | Ticket goes to Management/Work Team   |
| Reject                 | Ticket closed as rejected with reason |
| Need More Information  | Ticket goes back to user              |
| Change Priority        | Example: Medium to High               |
| Change Category / Area | If user selected wrong area           |
| Add Comment            | Internal approval note                |
| Select Team            | Choose which team will work           |

Important:
The authorized person should not need to work on the ticket. Their main job is **control and approval**.

---

## Step 3: Approved Ticket Goes to Management / Work Team

After approval:

```text
Status = Approved
Assigned Team = selected team
Ticket appears in Team Dashboard
Notification sent to Team Lead / Management Team
```

Team lead can:

| Action            | Result                               |
| ----------------- | ------------------------------------ |
| Assign to member  | Ticket goes to work person           |
| Set due date      | SLA tracking                         |
| Add internal note | Team discussion                      |
| Start work        | Status becomes In Progress           |
| Put on hold       | Waiting for dependency               |
| Ask user info     | Status becomes Need More Information |

---

## Step 4: Work Team Works on Ticket

Work team member updates:

| Field          | Purpose                           |
| -------------- | --------------------------------- |
| Work Note      | What work was done                |
| Technical Note | Internal technical details        |
| Status         | In Progress / On Hold / Completed |
| Attachment     | Proof, screenshot, updated file   |
| Time Spent     | Optional                          |
| Next Action    | What remains pending              |

Example note:

```text
Checked Lattice pricing calculation issue.
Problem found in P Price finalization logic.
Correction done and moved to testing.
```

---

## Step 5: Ticket Completion

When work is finished:

```text
Status = Completed
Resolution Note mandatory
Attachment/proof optional
Notification sent to Authorized Person + User
```

Completion fields:

| Field            | Required                    |
| ---------------- | --------------------------- |
| Resolution Note  | Yes                         |
| Completed By     | Auto                        |
| Completed Date   | Auto                        |
| Final Attachment | Optional                    |
| Root Cause       | Required for bug            |
| Release Note     | Required if software change |

---

## Step 6: Verification and Closure

Two options:

### Option A: Authorized Person closes

```text
Completed → Authorized Person checks → Closed
```

### Option B: User confirms closure

```text
Completed → User checks → User confirms → Closed
```

Recommended for your system:

```text
Completed → Authorized Person verifies → Closed
```

Because this keeps control centralized.

---

# 4. Final Status Definition

| Status                | Meaning                                 |
| --------------------- | --------------------------------------- |
| Draft                 | Ticket saved but not submitted          |
| Submitted             | User submitted ticket                   |
| Pending Authorization | Waiting for authorized person approval  |
| Need More Information | User must update missing details        |
| Approved              | Authorized person approved ticket       |
| Rejected              | Ticket rejected with reason             |
| Assigned to Team      | Ticket assigned to management/work team |
| In Progress           | Team started work                       |
| Work Updated          | Team added progress update              |
| On Hold               | Work paused                             |
| Completed             | Team completed work                     |
| Verified              | Authorized person/user verified         |
| Closed                | Ticket fully closed                     |
| Reopened              | Closed/completed ticket opened again    |
| Cancelled             | Ticket cancelled                        |
| Duplicate             | Same ticket already exists              |

---

# 5. Screen-Wise Requirement

## A. User Ticket Create Screen

Fields:

```text
System: Lattice / Trybe
Area: Module name
Category: Bug / New Requirement / Data Issue / Change Request
Priority: Urgent / High / Medium / Low
Title
Description
Attachment
Expected Date
Submit Button
Save as Draft Button
```

User can see:

```text
My Tickets
My Open Tickets
My Pending Tickets
My Completed Tickets
My Reopened Tickets
```

---

## B. Authorized Person Dashboard

This is the main control screen.

Cards:

```text
Pending Authorization
Approved Today
Rejected Today
Urgent Tickets
Pending More Information
Completed Waiting for Closure
Reopened Tickets
```

Table columns:

```text
Ticket No
System
Area
Category
Priority
Title
Created By
Created Date
Status
Action
```

Actions:

```text
View
Approve
Reject
Need More Information
Change Priority
Assign Team
Add Note
```

---

## C. Management / Team Dashboard

Only approved tickets should show here.

Cards:

```text
Approved Tickets
Assigned to My Team
In Progress
On Hold
Completed
SLA Delayed
```

Actions:

```text
Assign Member
Start Work
Add Work Note
Upload Attachment
Change Status
Mark Completed
```

---

## D. Ticket Detail Page

Ticket detail page must show full history.

Sections:

```text
Ticket Details
Approval Details
Assigned Team Details
Work Notes
Attachments
Status Timeline
Comments
Activity Log
Resolution Details
Reopen History
```

---

# 6. Permission Matrix

| Action             | User | Authorized Person | Team Lead | Work Member | Admin |
| ------------------ | ---: | ----------------: | --------: | ----------: | ----: |
| Create ticket      |  Yes |               Yes |       Yes |         Yes |   Yes |
| View own ticket    |  Yes |               Yes |       Yes |         Yes |   Yes |
| View all tickets   |   No |               Yes |  Optional |          No |   Yes |
| Approve ticket     |   No |               Yes |        No |          No |   Yes |
| Reject ticket      |   No |               Yes |        No |          No |   Yes |
| Assign team        |   No |               Yes |       Yes |          No |   Yes |
| Assign team member |   No |          Optional |       Yes |          No |   Yes |
| Add note           |  Yes |               Yes |       Yes |         Yes |   Yes |
| Update work status |   No |          Optional |       Yes |         Yes |   Yes |
| Mark completed     |   No |                No |       Yes |         Yes |   Yes |
| Close ticket       |   No |               Yes |  Optional |          No |   Yes |
| Reopen ticket      |  Yes |               Yes |       Yes |    Optional |   Yes |

---

# 7. Approval Logic

Use this simple logic:

```text
When ticket is created:
    status = Pending Authorization
    assigned_authorizer = default authorized person based on system/area
```

Example:

| System  | Area    | Authorized Person         |
| ------- | ------- | ------------------------- |
| Lattice | Pricing | Lattice Authorized Person |
| Lattice | Report  | Lattice Authorized Person |
| Trybe   | Labour  | Trybe Authorized Person   |
| Trybe   | Mapping | Trybe Authorized Person   |

After approval:

```text
status = Approved
assigned_team = selected team
visible_to_team = Yes
```

After team starts:

```text
status = In Progress
```

After team completes:

```text
status = Completed
```

After authorized person checks:

```text
status = Closed
```

---

# 8. Note / Update System

Every update should be saved as a note.

## Note Types

| Note Type       | Used By                  |
| --------------- | ------------------------ |
| User Comment    | Request user             |
| Approval Note   | Authorized person        |
| Work Note       | Team member              |
| Internal Note   | Team only                |
| Resolution Note | Work team                |
| Reopen Note     | User / authorized person |

Fields:

```text
ticket_id
note_type
note_text
created_by
created_at
visibility: Public / Internal
attachment_id
```

Important rule:

```text
User can see public notes only.
Team and Authorized Person can see public + internal notes.
```

---

# 9. Notification Requirement

Send notification when:

| Event                 | Receiver                 |
| --------------------- | ------------------------ |
| Ticket created        | Authorized Person        |
| Ticket approved       | User + Team Lead         |
| Ticket rejected       | User                     |
| Need more information | User                     |
| Assigned to team      | Team Lead                |
| Assigned to member    | Work Member              |
| Work note added       | Related users            |
| Status changed        | User + Authorized Person |
| Completed             | Authorized Person + User |
| Closed                | User + Team              |
| Reopened              | Authorized Person + Team |

---

# 10. Database Changes Required

## `tickets`

```sql
tickets
- id
- ticket_no
- system_id
- area_id
- category_id
- priority
- title
- description
- status
- created_by
- authorized_person_id
- approved_by
- approved_at
- rejected_by
- rejected_at
- rejection_reason
- assigned_team_id
- assigned_to
- due_date
- completed_by
- completed_at
- closed_by
- closed_at
- reopen_count
- created_at
- updated_at
```

## `ticket_notes`

```sql
ticket_notes
- id
- ticket_id
- note_type
- note_text
- visibility
- created_by
- created_at
```

## `ticket_approval_history`

```sql
ticket_approval_history
- id
- ticket_id
- action
- action_by
- action_at
- note
```

## `teams`

```sql
teams
- id
- team_name
- system_id
- team_lead_id
- is_active
```

## `team_members`

```sql
team_members
- id
- team_id
- user_id
- is_active
```

## `ticket_status_history`

```sql
ticket_status_history
- id
- ticket_id
- old_status
- new_status
- changed_by
- changed_at
- note
```

---

# 11. Simple Flow for Developer Implementation

```text
Create Ticket
    ↓
Save ticket with status = Pending Authorization
    ↓
Notify Authorized Person
    ↓
Authorized Person opens ticket
    ↓
Approve / Reject / Need Info
    ↓
If Approved:
    status = Approved
    assigned_team_id = selected team
    notify Team Lead
    ↓
Team Lead assigns member
    status = Assigned to Team
    ↓
Member starts work
    status = In Progress
    ↓
Member adds notes and attachments
    ↓
Member marks Completed
    ↓
Authorized Person verifies
    ↓
Close ticket
```

---

# 12. Final Requirement Statement

Implement the internal ticket system with a **single authorization-based workflow**. Any user can create a ticket for **Lattice** or **Trybe**. After creation, the ticket should first go to an **Authorized Person**, who can view all tickets and approve, reject, or ask for more information. Only approved tickets should be visible to the selected **Management/Work Team**. The team will work on the ticket, add notes, upload attachments, update progress, and mark the ticket as completed. After completion, the Authorized Person will verify and close the ticket. Reopen functionality must be available if the issue is not resolved.

This is the clean MVP flow you should implement first.
+======
for this We currently use theFirebase thing so i'll add that thing also so make env for other thing 