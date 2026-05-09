Yes, next phase should **not add more complex features**.
Next phase should make the system **easy for non-technical users**.

Current ticket flow is functionally correct, but if the user sees too many fields like assign, close, mandatory fields, status, team, verifier, internal notes, etc., they will get confused. So now we should do a **UX Simplification + UI Notification Phase** before implementing Gmail mail.

Your existing Lattice ticket export already has many fields such as **Activity, Area, Label, Priority, Status, Title, Assignee, Creator, Reporter, Verifier, Work Batch, Workspace Name**, and many statuses like **Open, Release, Completed, Closed, Later, To Do**. That is useful for backend tracking, but for normal users we should show only simple terms and hide technical fields. 
For Trybe, because users may raise issues around labour data, employee code, attendance, pcs, cts, amount, and mapping mismatch, the ticket form should guide users with ready-made options instead of expecting them to write technical details. 

---

# Next Phase: UX Simplification + UI Notification

## Phase Name

```text id="3b7drk"
Phase 3 — User-Friendly Ticket UX + In-App Notification UI
```

## Main Goal

Make the system usable for a **non-technical person**.

The user should feel:

```text id="5x3a31"
I know where to click.
I know what information to fill.
I know my ticket status.
I know who is working on it.
I know when action is required from me.
```

---

# 1. Main UX Problem to Fix

Currently the system has proper functionality, but it may feel difficult because of:

```text id="z2v7le"
Too many fields
Too many mandatory inputs
Too many buttons
Too many statuses
Too many dropdowns
Technical words
User does not know next step
User does not know who is responsible
User does not know whether ticket is pending, approved, or completed
```

So we should keep backend functionality, but simplify frontend.

---

# 2. New Simple User Flow

For normal user, show only this:

```text id="o6g6q6"
Create Ticket
↓
Track Ticket
↓
Reply if more information is needed
↓
Confirm if issue solved
```

For authorized person:

```text id="b2gv35"
Review New Tickets
↓
Approve / Send Back / Reject
↓
Track Completed Tickets
↓
Close Ticket
```

For team:

```text id="y8al59"
See Assigned Work
↓
Start Work
↓
Add Update
↓
Mark Done
```

---

# 3. Simplified Ticket Status for UI

Backend can keep detailed statuses, but frontend should show simple status labels.

## Backend Status vs User-Friendly Status

| Backend Status        | Show to User         |
| --------------------- | -------------------- |
| Pending Authorization | Waiting for Approval |
| Need More Information | Need Your Reply      |
| Approved              | Approved             |
| Assigned To Team      | Assigned to Team     |
| In Progress           | Work in Progress     |
| On Hold               | Waiting / On Hold    |
| Completed             | Work Done            |
| Verified              | Checked              |
| Closed                | Closed               |
| Reopened              | Reopened             |
| Rejected              | Rejected             |

Normal user should not see technical status like:

```text id="j8z4bk"
Assigned To Team
Verifier
Release
Internal Note
Audit Log
Status History
```

These can remain inside admin/detail section.

---

# 4. Simplified Ticket Create Form

## Current Problem

Too many fields make users confused.

## New Form Design

Use a **3-step form**.

---

## Step 1: What is the issue about?

Fields:

```text id="7dqqif"
System: Lattice / Trybe
Issue Type: Problem / New Request / Data Issue / Access Issue / Report Issue
Area: Auto-filter based on selected system
```

Use simple labels:

| Old Name    | New Label           |
| ----------- | ------------------- |
| Category    | Issue Type          |
| Priority    | How urgent is it?   |
| Description | Explain the issue   |
| Attachment  | Add screenshot/file |

---

## Step 2: Explain the issue

Fields:

```text id="p66ohu"
Title
Description
Attachment
```

Help text should show:

```text id="64o0z7"
Example: I am unable to upload lab result file.
Example: Trybe employee code is not matching.
Example: Lattice report is not loading.
```

---

## Step 3: Urgency

Instead of technical priority, show user-friendly options:

| User Selection        | Saved Priority |
| --------------------- | -------------- |
| Work stopped          | Urgent         |
| Important, need today | High           |
| Normal issue          | Medium         |
| Small change          | Low            |

This is easier than asking user to decide “Urgent / High / Medium / Low” directly.

---

# 5. Mandatory Field Reduction

## Required for Normal User

Only these should be mandatory:

```text id="2gz63o"
System
Issue Type
Area
Title
Description
Urgency
```

## Optional

```text id="xogbpv"
Attachment
Expected Date
Related ticket
Department
Stone ID / Employee Code / Report Name
```

Do not make assign person, close person, verifier, team, due date mandatory for normal user.

---

# 6. Smart Fields Based on System

## If user selects Lattice

Show optional fields:

```text id="zvsj2s"
Stone ID
Report Name
Module Name
Upload File Name
Screen/Page Name
```

Suggested Lattice templates:

```text id="qjn234"
Report not loading
File upload issue
Stone transfer issue
Pricing issue
User rights issue
Lab result issue
Sales issue
```

## If user selects Trybe

Show optional fields:

```text id="s6uq7h"
Employee Code
Month
Department
Attendance Issue
Pcs / Cts / Amount Issue
Mapping Issue
```

Suggested Trybe templates:

```text id="mn703b"
Employee mapping not found
Attendance mismatch
Labour amount mismatch
Employee code missing
Trybe transaction missing
Monthly labour report issue
```

This is important because Trybe issues may be raised by HR/labour/data users who may not write technical descriptions properly.

---

# 7. Button UX Improvement

## Normal User Buttons

Show only:

```text id="dcqv9k"
Create Ticket
Save Draft
Cancel
View Details
Reply
Reopen
```

Do not show:

```text id="5qrbgy"
Approve
Assign
Start Work
Complete
Close
Internal Note
Audit Log
```

---

## Authorized Person Buttons

Show only based on status:

### Waiting for Approval

```text id="7m26l7"
Approve
Send Back
Reject
```

Use **Send Back** instead of “Need More Information” because it is easier.

---

### Completed

```text id="57it1s"
Close Ticket
Reopen
Ask Team
```

---

## Team Buttons

Show only:

```text id="ihwn8l"
Start Work
Add Update
Put On Hold
Mark Done
```

Use **Mark Done** instead of “Completed”.

---

# 8. Role-Based Home Page

After login, each user should land on a simple page.

## Request User Home

Cards:

```text id="aez2eq"
Create New Ticket
My Open Tickets
Need My Reply
Closed Tickets
```

Main table:

```text id="hmhvbn"
My Recent Tickets
```

---

## Authorized Person Home

Cards:

```text id="f5w0gk"
Waiting for Approval
Sent Back Tickets
Completed Waiting Closure
Urgent Tickets
```

Main table:

```text id="yt67zl"
Tickets Needing My Action
```

---

## Team Home

Cards:

```text id="80o24u"
Assigned to Me
In Progress
On Hold
Done Today
```

Main table:

```text id="06u6q9"
My Work Queue
```

---

## Admin Home

Cards:

```text id="znmfs4"
Total Tickets
Open Tickets
Waiting Approval
In Progress
Closed
```

---

# 9. Ticket Detail Page UX

Ticket detail should have two modes.

## Simple View

For normal users:

```text id="fejqys"
Ticket No
Title
Current Status
Created Date
Assigned Team, if available
Latest Update
Conversation
Attachments
Action Needed
```

Do not show audit log or internal status history to normal user.

---

## Advanced View

For admin, authorized person, team lead:

```text id="wkkj89"
Full details
Approval history
Team assignment
Internal notes
Status history
Audit log
Attachments
Timeline
```

Use tabs:

```text id="yvqyz4"
Overview
Conversation
Updates
Attachments
History
```

---

# 10. Dropdown UX Improvement

## Problem

Long dropdowns are hard to use.

## Required Improvements

Use:

```text id="d3c8ov"
Searchable dropdown
Grouped dropdown
Default recent selection
Clear labels
Short descriptions
```

Example for Area:

```text id="wy2tk6"
Lattice
  - Pricing
  - Report
  - Lab Result
  - Sales
  - User Rights

Trybe
  - Labour
  - Employee Mapping
  - Attendance
  - Payroll
  - Monthly Report
```

Show only active areas. Hide inactive areas.

---

# 11. Table UX Improvement

Ticket list should be clean.

## Show Only Important Columns

For normal users:

```text id="bg9u9h"
Ticket No
Title
System
Status
Urgency
Last Update
Action
```

For authorized person:

```text id="emv3hp"
Ticket No
Title
System
Created By
Urgency
Status
Created Date
Action
```

For team:

```text id="1wrriq"
Ticket No
Title
System
Priority
Status
Assigned Date
Action
```

Extra columns should go inside detail page.

---

# 12. Search and Filter UX

Add simple filters:

```text id="s95gkk"
Search by ticket no / title
Status
System
Urgency
Date range
```

Use quick filter chips:

```text id="kg975t"
All
Open
Need My Action
Urgent
Closed
```

This is easier than many dropdown filters.

---

# 13. Notification UI — Before Mail

Now implement **in-app notification UI** first. Mail will come later.

## Notification Bell

Add bell icon in top header.

Show unread count:

```text id="n2jbw7"
🔔 5
```

Click bell shows dropdown:

```text id="hvo51y"
New ticket waiting for approval
Ticket KG-TKT-000021 was approved
Team added update on your ticket
Ticket needs your reply
Ticket marked done
```

Each notification should be clickable and open ticket detail page.

---

# 14. Notification Events

Create notification for these events.

| Event              | Receiver                         |
| ------------------ | -------------------------------- |
| Ticket created     | Authorized Person                |
| Ticket approved    | Request User + Team Lead         |
| Ticket sent back   | Request User                     |
| Ticket rejected    | Request User                     |
| Team assigned      | Team Lead                        |
| Member assigned    | Team Member                      |
| Work update added  | Request User + Authorized Person |
| Ticket marked done | Authorized Person + Request User |
| Ticket closed      | Request User + Team              |
| Ticket reopened    | Authorized Person + Team         |

---

# 15. Notification Firestore Collection

Use existing planned collection:

```text id="ao2vox"
notifications
```

Structure:

```json id="l2n0tz"
{
  "userId": "receiver_uid",
  "title": "Ticket needs your approval",
  "message": "KG-TKT-000021 is waiting for your approval.",
  "type": "TICKET_APPROVAL",
  "module": "Ticket",
  "recordId": "ticket_doc_id",
  "ticketNo": "KG-TKT-000021",
  "isRead": false,
  "createdAt": "timestamp",
  "createdBy": "system_or_user_uid"
}
```

---

# 16. Notification UI Pages

Add routes:

```text id="p1jlhl"
/notifications
/notifications/unread
```

## Notification Dropdown

Show last 5 notifications.

Actions:

```text id="t1dhkp"
Mark as read
View all
Open ticket
```

## Notification Page

Show full list:

```text id="ppp3d1"
All
Unread
Ticket Updates
Approvals
Assigned Work
```

---

# 17. Toast Messages

Add small success/error messages after every action.

Examples:

```text id="ue4jnp"
Ticket created successfully.
Ticket approved successfully.
Ticket sent back to user.
Work update added.
Ticket marked done.
```

Error examples:

```text id="dfgn1v"
Please enter title.
Please select issue type.
You do not have permission for this action.
Something went wrong. Please try again.
```

---

# 18. Empty State Design

When no data is available, show helpful message.

Examples:

```text id="oevtx7"
No tickets found.
You do not have any pending tickets.
No tickets need your action right now.
No notifications yet.
```

Add button when useful:

```text id="e1etmo"
Create New Ticket
Refresh
```

---

# 19. Confirmation Popups

Add confirmation before important actions.

## Reject Ticket

```text id="ljp04q"
Are you sure you want to reject this ticket?
Reason is required.
```

## Close Ticket

```text id="rjeh54"
Are you sure this ticket is solved and can be closed?
Closure note is optional.
```

## Reopen Ticket

```text id="8z61lr"
Why do you want to reopen this ticket?
Reason is required.
```

Avoid confirmation for simple updates like adding notes.

---

# 20. Final Simplified Workflow

## Normal User

```text id="0b1t4w"
1. Click Create Ticket
2. Select Lattice or Trybe
3. Select issue type
4. Add title and description
5. Select urgency
6. Submit
7. Track status
8. Reply if system asks for more information
9. Reopen only if issue is not solved
```

---

## Authorized Person

```text id="zs4lmt"
1. Open Waiting for Approval
2. Review ticket
3. Click Approve / Send Back / Reject
4. If approved, select team
5. Later close completed tickets
```

---

## Team

```text id="jkuvki"
1. Open My Work Queue
2. Click Start Work
3. Add update
4. Mark Done
```

---

# 21. Phase 3 Development Tasks

Follow this order.

```text id="94ootv"
1. Review current ticket screens
2. Hide unnecessary fields based on user type
3. Convert create ticket form into 3-step form
4. Rename technical labels into simple labels
5. Reduce mandatory fields
6. Add smart fields for Lattice and Trybe
7. Improve dropdowns with search and grouping
8. Improve ticket list columns by role
9. Add quick filters and search
10. Add role-based home cards
11. Improve ticket detail page with Simple View and Advanced View
12. Show action buttons only when allowed
13. Add confirmation popups for reject/close/reopen
14. Add toast success/error messages
15. Add notification bell in header
16. Create notifications collection save logic
17. Create notification dropdown
18. Create notification list page
19. Mark notification read/unread
20. Link notification to ticket detail
21. Test full flow with Request User, Authorized Person, Team Member, Admin
```

---

# 22. Phase 3 Acceptance Criteria

This phase is complete when:

```text id="wrx50f"
Normal user can create ticket without confusion.
Normal user does not see admin/team buttons.
Authorized person sees only approval-related actions.
Team member sees only work-related actions.
Ticket create form has fewer mandatory fields.
Lattice/Trybe specific fields appear only when needed.
Dropdowns are searchable and easy to understand.
Tables show only useful columns.
Action buttons are clear and status-based.
Notification bell shows unread count.
Notification dropdown opens latest notifications.
Notification click opens ticket detail.
Toast messages show after actions.
Non-technical user can use the system without training.
```

---

# 23. Mail Phase Should Come After This

Do **not** implement Gmail SMTP yet.

First complete:

```text id="gj7bny"
UI notification
Notification collection
Notification read/unread
Ticket action notification trigger
```

After this is stable, implement:

```text id="athmnh"
Gmail SMTP
Email queue
Email template
Send mail on ticket events
```

Reason: if UI notification logic is correct, mail implementation becomes easy because mail will use the same notification events.

---

# Final Developer Instruction

Implement **Phase 3 — UX Simplification + In-App Notification UI**. Do not add more complexity. Keep existing Firebase ticket data and backend fields, but simplify what users see. Normal users should only see simple ticket creation, tracking, reply, and reopen options. Authorized persons should only see approval and closure actions. Team users should only see work queue, updates, and mark-done actions. Add notification bell, notification dropdown, unread count, notification page, toast messages, simple labels, better dropdowns, role-based dashboards, and status-based buttons. After this phase is stable, we will implement Gmail SMTP mail.
