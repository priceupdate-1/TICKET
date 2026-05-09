import {
  AUTHORIZER_BY_SYSTEM_AREA,
  ROLES,
  VISIBILITY,
} from "./data.js";

function nowIso() {
  return new Date().toISOString();
}

function nextId(prefix) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

export function getUserById(state, userId) {
  return state.users.find((user) => user.id === userId);
}

export function getTeamById(state, teamId) {
  return state.teams.find((team) => team.id === teamId);
}

export function findDefaultAuthorizer(system, area) {
  return (
    AUTHORIZER_BY_SYSTEM_AREA.find(
      (entry) => entry.system === system && entry.area === area,
    )?.authorizerId ||
    AUTHORIZER_BY_SYSTEM_AREA.find((entry) => entry.system === system)?.authorizerId ||
    ""
  );
}

function isAdmin(user) {
  return user.role === ROLES.ADMIN || user.role === ROLES.SUPER_ADMIN;
}

function isAssignedTeamLead(state, user, ticket) {
  const team = getTeamById(state, ticket.assignedTeamId);
  return team?.teamLeadId === user.id;
}

function isAssignedWorkMember(state, user, ticket) {
  const team = getTeamById(state, ticket.assignedTeamId);
  return ticket.assignedTo === user.id || Boolean(team?.memberIds?.includes(user.id));
}

export function canAccessTicket(state, user, ticket) {
  if (!user || !ticket) {
    return false;
  }

  if (isAdmin(user)) {
    return true;
  }

  if (ticket.createdBy === user.id || ticket.authorizedPersonId === user.id) {
    return true;
  }

  if (isAssignedTeamLead(state, user, ticket) || isAssignedWorkMember(state, user, ticket)) {
    return true;
  }

  return false;
}

export function canPerform(state, user, action, ticket) {
  if (!user) {
    return false;
  }

  if (action === "create") {
    return true;
  }

  if (!ticket || !canAccessTicket(state, user, ticket)) {
    return false;
  }

  if (isAdmin(user)) {
    return true;
  }

  const isAuthorizer = ticket.authorizedPersonId === user.id;
  const isCreator = ticket.createdBy === user.id;
  const isLead = isAssignedTeamLead(state, user, ticket);
  const isWorker = isAssignedWorkMember(state, user, ticket);

  switch (action) {
    case "approve":
    case "reject":
    case "need-info":
    case "assign-team":
    case "close":
      return isAuthorizer;
    case "assign-member":
      return isLead || isAuthorizer;
    case "start-work":
    case "update-work":
    case "hold":
    case "complete":
      return isLead || isWorker;
    case "reopen":
      return isCreator || isAuthorizer || isLead;
    case "note-public":
      return true;
    case "note-internal":
      return !isCreator;
    default:
      return false;
  }
}

function addNotification(state, receiverId, message) {
  state.notifications.unshift({
    id: nextId("notify"),
    receiverId,
    message,
    createdAt: nowIso(),
  });
}

function addNote(state, ticket, user, noteType, noteText, visibility = VISIBILITY.PUBLIC) {
  if (!noteText.trim()) {
    return;
  }

  state.notes.unshift({
    id: nextId("note"),
    ticketId: ticket.id,
    noteType,
    noteText: noteText.trim(),
    visibility,
    createdBy: user.id,
    createdAt: nowIso(),
  });
}

function addApprovalHistory(state, ticketId, action, userId, note) {
  state.approvalHistory.unshift({
    id: nextId("approval"),
    ticketId,
    action,
    actionBy: userId,
    actionAt: nowIso(),
    note: note?.trim() || "",
  });
}

function addStatusHistory(state, ticket, userId, nextStatus, note) {
  state.statusHistory.unshift({
    id: nextId("history"),
    ticketId: ticket.id,
    oldStatus: ticket.status,
    newStatus: nextStatus,
    changedBy: userId,
    changedAt: nowIso(),
    note: note?.trim() || "",
  });
  ticket.status = nextStatus;
}

function touchState(state, ticket) {
  ticket.updatedAt = nowIso();
  state.meta.lastSavedAt = nowIso();
}

function resolveUserName(state, userId) {
  return getUserById(state, userId)?.name || "System";
}

function getTicket(state, ticketId) {
  return state.tickets.find((entry) => entry.id === ticketId);
}

export function getVisibleTickets(state, user) {
  if (!user) {
    return [];
  }

  if (isAdmin(user)) {
    return [...state.tickets];
  }

  return state.tickets.filter((ticket) => canAccessTicket(state, user, ticket));
}

export function createTicket(state, user, payload) {
  const nextNumber = state.meta.lastTicketNumber + 1;
  const ticketId = nextId("ticket");
  const authorizerId = findDefaultAuthorizer(payload.system, payload.area);
  const authorizer = getUserById(state, authorizerId);

  const ticket = {
    id: ticketId,
    ticketNo: `TKT-${nextNumber}`,
    system: payload.system,
    area: payload.area,
    category: payload.category,
    priority: payload.priority,
    title: payload.title.trim(),
    description: payload.description.trim(),
    status: "Pending Authorization",
    createdBy: user.id,
    authorizedPersonId: authorizerId,
    approvedBy: "",
    approvedAt: "",
    rejectedBy: "",
    rejectedAt: "",
    rejectionReason: "",
    assignedTeamId: "",
    assignedTo: "",
    dueDate: payload.dueDate || "",
    expectedDate: payload.expectedDate || "",
    completedBy: "",
    completedAt: "",
    closedBy: "",
    closedAt: "",
    reopenCount: 0,
    attachmentNames: payload.attachmentName ? [payload.attachmentName] : [],
    label: `${payload.system.toUpperCase().slice(0, 3)}-${payload.area.toUpperCase().slice(0, 3)}`,
    reporter: user.name,
    verifier: authorizer?.name || "",
    workBatch: payload.workBatch || "",
    workspaceName: payload.workspaceName || "",
    resolutionNote: "",
    rootCause: "",
    createdAt: nowIso(),
    updatedAt: nowIso(),
  };

  state.tickets.unshift(ticket);
  state.meta.lastTicketNumber = nextNumber;

  addStatusHistory(state, { ...ticket, status: "Submitted" }, user.id, "Pending Authorization", "Ticket submitted for authorization.");
  addNote(state, ticket, user, "User Comment", payload.description, VISIBILITY.PUBLIC);

  if (authorizerId) {
    addNotification(
      state,
      authorizerId,
      `${ticket.ticketNo} created by ${user.name} and waiting for authorization.`,
    );
  }

  touchState(state, ticket);
  return ticket;
}

export function approveTicket(state, user, ticketId, payload) {
  const ticket = getTicket(state, ticketId);
  if (!ticket) {
    return null;
  }

  if (payload.priority) {
    ticket.priority = payload.priority;
  }

  if (payload.teamId) {
    ticket.assignedTeamId = payload.teamId;
  }

  ticket.approvedBy = user.id;
  ticket.approvedAt = nowIso();
  ticket.rejectedBy = "";
  ticket.rejectedAt = "";
  ticket.rejectionReason = "";
  addStatusHistory(state, ticket, user.id, "Approved", payload.note || "Approved for team delivery.");
  addApprovalHistory(state, ticket.id, "Approved", user.id, payload.note || "");
  addNote(state, ticket, user, "Approval Note", payload.note || "Ticket approved.", VISIBILITY.INTERNAL);

  const team = getTeamById(state, ticket.assignedTeamId);
  if (team?.teamLeadId) {
    addNotification(
      state,
      team.teamLeadId,
      `${ticket.ticketNo} approved and ready for ${team.teamName}.`,
    );
  }

  touchState(state, ticket);
  return ticket;
}

export function rejectTicket(state, user, ticketId, reason) {
  const ticket = getTicket(state, ticketId);
  if (!ticket) {
    return null;
  }

  ticket.rejectedBy = user.id;
  ticket.rejectedAt = nowIso();
  ticket.rejectionReason = reason.trim();
  addStatusHistory(state, ticket, user.id, "Rejected", reason);
  addApprovalHistory(state, ticket.id, "Rejected", user.id, reason);
  addNote(state, ticket, user, "Approval Note", reason, VISIBILITY.PUBLIC);
  addNotification(state, ticket.createdBy, `${ticket.ticketNo} was rejected. Reason: ${reason.trim()}`);
  touchState(state, ticket);
  return ticket;
}

export function requestMoreInformation(state, user, ticketId, note) {
  const ticket = getTicket(state, ticketId);
  if (!ticket) {
    return null;
  }

  addStatusHistory(state, ticket, user.id, "Need More Information", note);
  addApprovalHistory(state, ticket.id, "Need More Information", user.id, note);
  addNote(state, ticket, user, "Approval Note", note, VISIBILITY.PUBLIC);
  addNotification(
    state,
    ticket.createdBy,
    `${ticket.ticketNo} needs more information from requester.`,
  );
  touchState(state, ticket);
  return ticket;
}

export function assignTeam(state, user, ticketId, teamId, note) {
  const ticket = getTicket(state, ticketId);
  const team = getTeamById(state, teamId);
  if (!ticket || !team) {
    return null;
  }

  ticket.assignedTeamId = teamId;
  addStatusHistory(
    state,
    ticket,
    user.id,
    "Assigned to Team",
    note || `Assigned to ${team.teamName}.`,
  );
  addNote(
    state,
    ticket,
    user,
    "Internal Note",
    note || `Ticket routed to ${team.teamName}.`,
    VISIBILITY.INTERNAL,
  );
  addNotification(state, team.teamLeadId, `${ticket.ticketNo} assigned to your team.`);
  touchState(state, ticket);
  return ticket;
}

export function assignMember(state, user, ticketId, memberId, dueDate, note) {
  const ticket = getTicket(state, ticketId);
  if (!ticket) {
    return null;
  }

  ticket.assignedTo = memberId;
  ticket.dueDate = dueDate || ticket.dueDate;
  if (ticket.status === "Approved") {
    addStatusHistory(state, ticket, user.id, "Assigned to Team", note || "Team member assigned.");
  }
  addNote(
    state,
    ticket,
    user,
    "Internal Note",
    note || `Assigned to ${resolveUserName(state, memberId)}.`,
    VISIBILITY.INTERNAL,
  );
  addNotification(
    state,
    memberId,
    `${ticket.ticketNo} assigned to you for execution.`,
  );
  touchState(state, ticket);
  return ticket;
}

export function startWork(state, user, ticketId, note) {
  const ticket = getTicket(state, ticketId);
  if (!ticket) {
    return null;
  }

  addStatusHistory(state, ticket, user.id, "In Progress", note || "Work started.");
  addNote(state, ticket, user, "Work Note", note || "Work started.", VISIBILITY.PUBLIC);
  addNotification(
    state,
    ticket.authorizedPersonId,
    `${ticket.ticketNo} is now in progress.`,
  );
  touchState(state, ticket);
  return ticket;
}

export function updateWork(state, user, ticketId, payload) {
  const ticket = getTicket(state, ticketId);
  if (!ticket) {
    return null;
  }

  const nextStatus = payload.status || "Work Updated";
  addStatusHistory(state, ticket, user.id, nextStatus, payload.note || "Progress updated.");
  addNote(
    state,
    ticket,
    user,
    payload.noteType || "Work Note",
    payload.note || "Progress updated.",
    payload.visibility || VISIBILITY.PUBLIC,
  );
  addNotification(
    state,
    ticket.authorizedPersonId,
    `${ticket.ticketNo} has a new work update.`,
  );
  touchState(state, ticket);
  return ticket;
}

export function completeTicket(state, user, ticketId, payload) {
  const ticket = getTicket(state, ticketId);
  if (!ticket) {
    return null;
  }

  ticket.completedBy = user.id;
  ticket.completedAt = nowIso();
  ticket.resolutionNote = payload.resolutionNote.trim();
  ticket.rootCause = payload.rootCause.trim();
  if (payload.attachmentName?.trim()) {
    ticket.attachmentNames = [...ticket.attachmentNames, payload.attachmentName.trim()];
  }
  addStatusHistory(state, ticket, user.id, "Completed", payload.resolutionNote);
  addNote(state, ticket, user, "Resolution Note", payload.resolutionNote, VISIBILITY.PUBLIC);
  addNotification(
    state,
    ticket.authorizedPersonId,
    `${ticket.ticketNo} marked completed and waiting for verification.`,
  );
  addNotification(state, ticket.createdBy, `${ticket.ticketNo} marked completed.`);
  touchState(state, ticket);
  return ticket;
}

export function verifyAndCloseTicket(state, user, ticketId, note) {
  const ticket = getTicket(state, ticketId);
  if (!ticket) {
    return null;
  }

  addStatusHistory(state, ticket, user.id, "Verified", note || "Verified by authorized person.");
  addStatusHistory(state, ticket, user.id, "Closed", note || "Ticket closed.");
  ticket.closedBy = user.id;
  ticket.closedAt = nowIso();
  addNote(state, ticket, user, "Approval Note", note || "Verified and closed.", VISIBILITY.PUBLIC);
  addNotification(state, ticket.createdBy, `${ticket.ticketNo} has been closed.`);
  if (ticket.assignedTo) {
    addNotification(state, ticket.assignedTo, `${ticket.ticketNo} has been closed after verification.`);
  }
  touchState(state, ticket);
  return ticket;
}

export function reopenTicket(state, user, ticketId, note) {
  const ticket = getTicket(state, ticketId);
  if (!ticket) {
    return null;
  }

  ticket.reopenCount += 1;
  ticket.closedBy = "";
  ticket.closedAt = "";
  addStatusHistory(state, ticket, user.id, "Reopened", note || "Ticket reopened.");
  addNote(state, ticket, user, "Reopen Note", note || "Ticket reopened.", VISIBILITY.PUBLIC);
  addNotification(
    state,
    ticket.authorizedPersonId,
    `${ticket.ticketNo} reopened by ${user.name}.`,
  );
  if (ticket.assignedTeamId) {
    const team = getTeamById(state, ticket.assignedTeamId);
    if (team?.teamLeadId) {
      addNotification(state, team.teamLeadId, `${ticket.ticketNo} reopened and needs review.`);
    }
  }
  touchState(state, ticket);
  return ticket;
}

export function appendGeneralNote(state, user, ticketId, payload) {
  const ticket = getTicket(state, ticketId);
  if (!ticket) {
    return null;
  }

  addNote(
    state,
    ticket,
    user,
    payload.noteType,
    payload.noteText,
    payload.visibility,
  );
  touchState(state, ticket);
  return ticket;
}
