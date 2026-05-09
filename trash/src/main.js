import { getAppConfig, loadOptionalRuntimeConfig } from "./config.js";
import { AREA_OPTIONS, CATEGORY_OPTIONS, createSeedState, NOTE_TYPES, PRIORITY_OPTIONS, ROLES, STATUS_ORDER, STATUS_LABELS, SYSTEMS, URGENCY_OPTIONS, VISIBILITY } from "./data.js";
import { createFirebaseAdapter } from "./firebase.js";
import { createLocalAdapter } from "./store.js";
import { appendGeneralNote, approveTicket, assignMember, assignTeam, canPerform, completeTicket, createTicket, getTeamById, getUserById, getVisibleTickets, rejectTicket, reopenTicket, requestMoreInformation, startWork, updateWork, verifyAndCloseTicket } from "./workflows.js";

const app = document.querySelector("#app");
let config, adapter, state;

const uiState = {
  selectedTicketId: "",
  activeChip: "All",
  filters: { query: "", status: "All", system: "All" },
  createStep: 1,
  createSystem: "Lattice",
  createUrgency: "Medium",
  notifOpen: false,
  modal: null,
  detailTab: "Overview",
};

function esc(v = "") {
  return String(v).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;");
}

function fmt(d, time) {
  if (!d) return "—";
  return new Intl.DateTimeFormat("en-IN", { dateStyle:"medium", timeStyle: time ? "short" : undefined }).format(new Date(d));
}

function timeAgo(d) {
  if (!d) return "";
  const diff = (Date.now() - new Date(d).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff/86400)}d ago`;
  return fmt(d);
}

function stClass(s) { return `status-${s.toLowerCase().replaceAll(" ","-")}`; }
function stLabel(s) { return STATUS_LABELS[s] || s; }
function currentUser() { return getUserById(state, state.meta.currentUserId) || state.users[0]; }
function isAdminLike(u) { return u.role === ROLES.ADMIN || u.role === ROLES.SUPER_ADMIN; }
function isAuthLike(u) { return u.role === ROLES.AUTHORIZED_PERSON; }
function isTeamLike(u) { return u.role === ROLES.TEAM_LEAD || u.role === ROLES.WORK_MEMBER; }
function isRequester(u) { return u.role === ROLES.REQUEST_USER; }

function getUnreadCount(user) {
  const notifs = state.notifications || [];
  if (isAdminLike(user)) return notifs.filter(n => !n.isRead).length;
  return notifs.filter(n => n.receiverId === user.id && !n.isRead).length;
}

function getUserNotifs(user) {
  const all = state.notifications || [];
  if (isAdminLike(user)) return all.slice(0, 12);
  return all.filter(n => n.receiverId === user.id).slice(0, 12);
}

function normalizeStateShape(loaded) {
  const seed = createSeedState();
  return {
    ...seed, ...loaded,
    meta: { ...seed.meta, ...(loaded.meta || {}) },
    users: loaded.users || seed.users,
    teams: loaded.teams || seed.teams,
    tickets: loaded.tickets || seed.tickets,
    notes: loaded.notes || seed.notes,
    approvalHistory: loaded.approvalHistory || seed.approvalHistory,
    statusHistory: loaded.statusHistory || seed.statusHistory,
    notifications: (loaded.notifications || seed.notifications).map(n => ({ isRead: false, title: n.message || "", ...n })),
  };
}

function sortByUpdate(tickets) { return [...tickets].sort((a,b) => new Date(b.updatedAt) - new Date(a.updatedAt)); }

function getFiltered() {
  const user = currentUser();
  const visible = getVisibleTickets(state, user);
  const chip = uiState.activeChip;
  return sortByUpdate(visible.filter(t => {
    const qOk = !uiState.filters.query || `${t.ticketNo} ${t.title} ${t.area} ${t.system}`.toLowerCase().includes(uiState.filters.query.toLowerCase());
    const sysOk = uiState.filters.system === "All" || t.system === uiState.filters.system;
    let chipOk = true;
    if (chip === "Open") chipOk = ["Pending Authorization","Approved","Assigned to Team","In Progress","Work Updated","Reopened"].includes(t.status);
    else if (chip === "Need My Action") {
      if (isRequester(user)) chipOk = ["Need More Information"].includes(t.status) && t.createdBy === user.id;
      else if (isAuthLike(user)) chipOk = ["Pending Authorization","Completed"].includes(t.status) && t.authorizedPersonId === user.id;
      else if (isTeamLike(user)) chipOk = ["Approved","Assigned to Team","In Progress","Work Updated","Reopened"].includes(t.status);
      else chipOk = ["Pending Authorization","Completed","Need More Information"].includes(t.status);
    }
    else if (chip === "Urgent") chipOk = t.priority === "Urgent";
    else if (chip === "Closed") chipOk = ["Closed","Completed","Verified","Rejected"].includes(t.status);
    return qOk && sysOk && chipOk;
  }));
}

function ensureSel(tickets) {
  if (!tickets.find(t => t.id === uiState.selectedTicketId))
    uiState.selectedTicketId = tickets[0]?.id || "";
}

function countBy(tickets, statuses) { return tickets.filter(t => statuses.includes(t.status)).length; }

function getVisibleNotes(ticket, user) {
  return (state.notes || []).filter(n => n.ticketId === ticket.id)
    .filter(n => user.role !== ROLES.REQUEST_USER || n.visibility === VISIBILITY.PUBLIC);
}

function getMemberOptions(teamId) {
  const team = getTeamById(state, teamId);
  if (!team) return [];
  return [team.teamLeadId, ...(team.memberIds || [])].map(id => getUserById(state, id)).filter(Boolean);
}

function renderOptions(opts, sel = "") {
  return opts.map(o => `<option value="${esc(o)}" ${sel===o?"selected":""}>${esc(o)}</option>`).join("");
}

// ── TOAST ──────────────────────────────────────────────────────────
function showToast(msg, type = "success") {
  const c = document.getElementById("toast-container");
  if (!c) return;
  const icon = type === "success" ? "✓" : "✕";
  const div = document.createElement("div");
  div.className = `toast toast-${type}`;
  div.innerHTML = `<span class="toast-icon">${icon}</span><span class="toast-msg">${esc(msg)}</span><button class="toast-close">✕</button>`;
  div.querySelector(".toast-close").onclick = () => div.remove();
  c.appendChild(div);
  setTimeout(() => div.remove(), 4000);
}

// ── PERSIST ────────────────────────────────────────────────────────
async function persist() {
  try { await adapter.save(state); }
  catch (e) { console.warn("persist failed", e); showToast("Could not save changes.", "error"); }
}

// ── NAVBAR ─────────────────────────────────────────────────────────
function renderNavbar() {
  const user = currentUser();
  const unread = getUnreadCount(user);
  const initials = user.name.split(" ").map(p => p[0]).slice(0,2).join("").toUpperCase();
  const modeWarn = adapter.mode !== "firebase";
  const modeText = adapter.mode === "firebase" ? "Firebase Sync" : "Local Storage";

  const roleOpts = state.users.map(u =>
    `<option value="${esc(u.id)}" ${u.id===user.id?"selected":""}>${esc(u.name)} — ${esc(u.role)}</option>`
  ).join("");

  return `
    <nav class="navbar">
      <div class="navbar-brand">
        <span class="brand-dot"></span>
        <span>KG Ticket Control</span>
      </div>
      <div class="navbar-right">
        <span class="mode-badge ${modeWarn?'is-warning':''}" title="${esc(adapter.warning || '')}">${esc(modeText)}</span>
        <div class="role-selector-wrap">
          <label>Logged in as</label>
          <select id="role-select">${roleOpts}</select>
        </div>
        <div class="bell-wrap">
          <button class="bell-btn" id="bell-btn" aria-label="Notifications">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>
            ${unread > 0 ? `<span class="bell-count">${unread}</span>` : ""}
          </button>
          ${renderNotifDropdown(user)}
        </div>
        <div class="user-chip">
          <span class="user-avatar">${esc(initials)}</span>
          <span>${esc(user.name)}</span>
          <span class="role-badge">${esc(user.role)}</span>
        </div>
      </div>
    </nav>`;
}

function renderNotifDropdown(user) {
  const notifs = getUserNotifs(user);
  const open = uiState.notifOpen ? "is-open" : "";
  const items = notifs.length === 0
    ? `<div class="notif-empty">No notifications yet.</div>`
    : notifs.map(n => `
        <div class="notif-item ${n.isRead?'':'unread'}" data-notif-id="${esc(n.id)}" data-ticket-id="${esc(n.recordId || '')}">
          <div class="notif-title">${esc(n.title || n.message || '')}</div>
          ${n.message && n.message !== n.title ? `<div class="small">${esc(n.message)}</div>`:""}
          <div class="notif-time">${esc(timeAgo(n.createdAt))}</div>
        </div>`).join("");

  return `
    <div class="notif-dropdown ${open}" id="notif-dropdown">
      <div class="notif-header">
        <div class="notif-header-title">Notifications</div>
        <button class="btn btn-ghost btn-sm" id="notif-mark-all">Mark all read</button>
      </div>
      <div>${items}</div>
      <div class="notif-footer" id="notif-clear-all">Clear all</div>
    </div>`;
}

// ── HOME CARDS (role-based) ────────────────────────────────────────
function renderStatCards() {
  const user = currentUser();
  const visible = getVisibleTickets(state, user);
  const myTickets = state.tickets.filter(t => t.createdBy === user.id);

  let cards = [];

  if (isRequester(user)) {
    cards = [
      { label: "My Open Tickets", value: countBy(myTickets, ["Pending Authorization","Approved","Assigned to Team","In Progress","Work Updated","Reopened"]), foot: "Currently active", cls: "is-brand" },
      { label: "Need My Reply",   value: countBy(myTickets, ["Need More Information"]),                                                                          foot: "Waiting on you",  cls: "is-danger" },
      { label: "Closed",          value: countBy(myTickets, ["Closed","Verified"]),                                                                              foot: "Resolved",        cls: "is-success" },
      { label: "Total Created",   value: myTickets.length,                                                                                                       foot: "All time",        cls: "is-teal" },
    ];
  } else if (isAuthLike(user)) {
    const queue = visible.filter(t => t.authorizedPersonId === user.id);
    cards = [
      { label: "Waiting Approval",   value: countBy(queue, ["Pending Authorization"]),     foot: "Action needed",     cls: "is-brand" },
      { label: "Need Info Pending",  value: countBy(queue, ["Need More Information"]),     foot: "Sent back to user", cls: "is-danger" },
      { label: "Done — Awaiting Closure", value: countBy(queue, ["Completed"]),            foot: "Verify and close",  cls: "is-teal" },
      { label: "Urgent",             value: queue.filter(t => t.priority === "Urgent").length, foot: "High priority", cls: "is-success" },
    ];
  } else if (isTeamLike(user)) {
    const queue = visible.filter(t => ["Approved","Assigned to Team","In Progress","Work Updated","Reopened","On Hold"].includes(t.status));
    const today = visible.filter(t => t.completedAt && new Date(t.completedAt).toDateString() === new Date().toDateString()).length;
    cards = [
      { label: "Assigned to Me", value: queue.filter(t => t.assignedTo === user.id).length, foot: "Personal queue", cls: "is-brand" },
      { label: "In Progress",    value: countBy(queue, ["In Progress","Work Updated"]),     foot: "Active work",    cls: "is-teal" },
      { label: "On Hold",        value: countBy(queue, ["On Hold"]),                        foot: "Paused",         cls: "is-danger" },
      { label: "Done Today",     value: today,                                              foot: "Completed",      cls: "is-success" },
    ];
  } else {
    cards = [
      { label: "Total Tickets",      value: state.tickets.length,                                                  foot: "All systems",    cls: "is-teal" },
      { label: "Waiting Approval",   value: countBy(state.tickets, ["Pending Authorization"]),                     foot: "Need decision",  cls: "is-brand" },
      { label: "In Progress",        value: countBy(state.tickets, ["Approved","Assigned to Team","In Progress","Work Updated"]), foot: "Active work", cls: "is-success" },
      { label: "Closed",             value: countBy(state.tickets, ["Closed","Verified"]),                         foot: "Resolved",       cls: "is-danger" },
    ];
  }

  return `
    <div class="stat-cards">
      ${cards.map(c => `
        <div class="stat-card ${c.cls}">
          <div class="stat-label">${esc(c.label)}</div>
          <div class="stat-value">${c.value}</div>
          <div class="stat-foot">${esc(c.foot)}</div>
        </div>`).join("")}
    </div>`;
}

// ── PAGE HEADER ────────────────────────────────────────────────────
function renderPageHeader() {
  const user = currentUser();
  let title = "Ticket Workspace", subtitle = "Track, approve and resolve work.";
  if (isRequester(user))     { title = `Hi ${user.name.split(" ")[0]}`;       subtitle = "Create a ticket, track status, and reply when asked."; }
  else if (isAuthLike(user)) { title = "Approval Desk";                       subtitle = "Review new tickets, approve or send back, and close completed work."; }
  else if (isTeamLike(user)) { title = "My Work Queue";                       subtitle = "Start work, post updates, and mark items done."; }
  else                       { title = "Admin Console";                       subtitle = "All tickets across Lattice and Trybe — direct controls below."; }

  return `
    <div class="page-header">
      <div>
        <h1 class="page-title">${esc(title)}</h1>
        <div class="page-subtitle">${esc(subtitle)}</div>
      </div>
    </div>`;
}

// ── ADMIN PENDING INLINE PANEL ─────────────────────────────────────
function renderAdminPendingPanel() {
  const user = currentUser();
  if (!isAdminLike(user) && !isAuthLike(user)) return "";

  const list = state.tickets
    .filter(t => t.status === "Pending Authorization")
    .filter(t => isAdminLike(user) || t.authorizedPersonId === user.id)
    .slice(0, 6);

  if (list.length === 0) {
    return `
      <div class="panel">
        <div class="panel-header"><span class="panel-title">Waiting for Approval</span></div>
        <div class="empty-state">
          <div class="empty-icon">✓</div>
          <div class="empty-msg">No tickets need your approval right now.</div>
        </div>
      </div>`;
  }

  return `
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Waiting for Approval (${list.length})</span>
      </div>
      <div class="panel-body">
        ${list.map(t => `
          <div class="pending-card" data-pending-id="${esc(t.id)}">
            <div class="pending-card-top">
              <div>
                <div class="pending-no">${esc(t.ticketNo)} · ${esc(t.system)} / ${esc(t.area)}</div>
                <div class="pending-title">${esc(t.title)}</div>
                <div class="pending-meta">From ${esc(getUserById(state, t.createdBy)?.name || "—")} · ${esc(timeAgo(t.createdAt))} · ${esc(t.priority)}</div>
              </div>
              <span class="status-pill ${stClass(t.status)}">${esc(stLabel(t.status))}</span>
            </div>
            <div class="pending-actions">
              <button class="btn btn-primary btn-sm" data-act="approve-quick" data-id="${esc(t.id)}">Approve</button>
              <button class="btn btn-secondary btn-sm" data-act="sendback-quick" data-id="${esc(t.id)}">Send Back</button>
              <button class="btn btn-danger btn-sm" data-act="reject-quick" data-id="${esc(t.id)}">Reject</button>
              <button class="btn btn-ghost btn-sm" data-act="open-detail" data-id="${esc(t.id)}">Open</button>
            </div>
          </div>`).join("")}
      </div>
    </div>`;
}

// ── 3-STEP CREATE FORM ─────────────────────────────────────────────
function renderCreateForm() {
  const user = currentUser();
  if (!canPerform(state, user, "create")) return "";
  const step = uiState.createStep;
  const sys = uiState.createSystem;
  const areas = AREA_OPTIONS[sys] || [];
  const issueTypes = ["Problem / Bug", "New Request", "Data Issue", "Access Issue", "Report Issue"];

  const smartFields = sys === "Lattice" ? `
    <div class="field"><label>Stone ID (optional)</label><input id="cf-stone" placeholder="e.g. ST-1024" /></div>
    <div class="field"><label>Report / Module (optional)</label><input id="cf-module" placeholder="e.g. Pricing report" /></div>
  ` : `
    <div class="field"><label>Employee Code (optional)</label><input id="cf-empcode" placeholder="e.g. EMP-2231" /></div>
    <div class="field"><label>Month (optional)</label><input id="cf-month" placeholder="e.g. May 2026" /></div>
  `;

  const templates = sys === "Lattice"
    ? ["Report not loading","File upload issue","Stone transfer issue","Pricing issue","User rights issue"]
    : ["Employee mapping not found","Attendance mismatch","Labour amount mismatch","Employee code missing","Monthly labour report issue"];

  const steps = ["What", "Details", "Urgency"];

  return `
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Create New Ticket</span>
      </div>
      <div class="form-steps">
        ${steps.map((s,i) => {
          const n = i+1;
          const cls = n===step?"is-active":(n<step?"is-done":"");
          return `<div class="form-step ${cls}"><span class="step-num">${n}</span>${esc(s)}</div>`;
        }).join("")}
      </div>

      <!-- STEP 1 -->
      <div class="form-page ${step===1?'':'is-hidden'}">
        <div class="field">
          <label>System</label>
          <select id="cf-system">${renderOptions(SYSTEMS, sys)}</select>
        </div>
        <div class="field">
          <label>Issue Type</label>
          <select id="cf-issue-type">${renderOptions(issueTypes)}</select>
        </div>
        <div class="field">
          <label>Area</label>
          <select id="cf-area">${renderOptions(areas)}</select>
        </div>
        <div class="field">
          <label>Common Templates (click to use)</label>
          <div class="button-row">
            ${templates.map(t => `<button class="chip" data-template="${esc(t)}">${esc(t)}</button>`).join("")}
          </div>
        </div>
        <div class="button-row">
          <button class="btn btn-primary" id="cf-next-1">Continue</button>
        </div>
      </div>

      <!-- STEP 2 -->
      <div class="form-page ${step===2?'':'is-hidden'}">
        <div class="field">
          <label>Title</label>
          <input id="cf-title" placeholder="Short summary" />
          <div class="field-hint">Example: I am unable to upload lab result file.</div>
        </div>
        <div class="field">
          <label>Explain the issue</label>
          <textarea id="cf-desc" placeholder="What happened? What did you expect?"></textarea>
        </div>
        <div class="field-grid">
          ${smartFields}
        </div>
        <div class="field">
          <label>Add screenshot / file (optional)</label>
          <input id="cf-attach" placeholder="filename.png" />
        </div>
        <div class="button-row">
          <button class="btn btn-ghost" id="cf-back-2">Back</button>
          <button class="btn btn-primary" id="cf-next-2">Continue</button>
        </div>
      </div>

      <!-- STEP 3 -->
      <div class="form-page ${step===3?'':'is-hidden'}">
        <div class="field"><label>How urgent is it?</label></div>
        <div class="urgency-grid">
          ${URGENCY_OPTIONS.map(o => `
            <div class="urgency-opt ${uiState.createUrgency===o.priority?'is-sel':''}" data-urg="${esc(o.priority)}">
              <div class="urg-title">${esc(o.label)}</div>
              <div class="urg-sub">${esc(o.sub)}</div>
            </div>`).join("")}
        </div>
        <div class="button-row">
          <button class="btn btn-ghost" id="cf-back-3">Back</button>
          <button class="btn btn-primary" id="cf-submit">Create Ticket</button>
        </div>
      </div>
    </div>`;
}

// ── FILTERS ────────────────────────────────────────────────────────
function renderFilters() {
  const chips = ["All","Open","Need My Action","Urgent","Closed"];
  return `
    <div class="filter-chips">
      ${chips.map(c => `<span class="chip ${uiState.activeChip===c?'is-active':''}" data-chip="${esc(c)}">${esc(c)}</span>`).join("")}
    </div>
    <div class="filter-row">
      <input id="filter-q" placeholder="Search by ticket no or title…" value="${esc(uiState.filters.query)}" />
      <select id="filter-sys">
        <option value="All" ${uiState.filters.system==="All"?"selected":""}>All Systems</option>
        ${renderOptions(SYSTEMS, uiState.filters.system)}
      </select>
      <button class="btn btn-ghost" id="filter-clear">Clear</button>
    </div>`;
}

// ── TICKET TABLE ───────────────────────────────────────────────────
function renderTicketTable() {
  const user = currentUser();
  const tickets = getFiltered();
  ensureSel(tickets);

  if (tickets.length === 0) {
    return `<div class="empty-state">
      <div class="empty-icon">📭</div>
      <div class="empty-msg">No tickets match these filters.</div>
      <button class="btn btn-secondary" id="filter-reset">Reset Filters</button>
    </div>`;
  }

  const cols = isRequester(user)
    ? ["Ticket","Title","System","Status","Urgency","Updated"]
    : isTeamLike(user)
      ? ["Ticket","Title","System","Priority","Status","Assigned","Updated"]
      : ["Ticket","Title","System","From","Priority","Status","Updated"];

  const rows = tickets.map(t => {
    const reporter = getUserById(state, t.createdBy)?.name || "—";
    const assignee = getUserById(state, t.assignedTo)?.name || "—";
    const cells = isRequester(user)
      ? [t.ticketNo, t.title, t.system, `<span class="status-pill ${stClass(t.status)}">${stLabel(t.status)}</span>`, t.priority, timeAgo(t.updatedAt)]
      : isTeamLike(user)
        ? [t.ticketNo, t.title, t.system, t.priority, `<span class="status-pill ${stClass(t.status)}">${stLabel(t.status)}</span>`, assignee, timeAgo(t.updatedAt)]
        : [t.ticketNo, t.title, t.system, reporter, t.priority, `<span class="status-pill ${stClass(t.status)}">${stLabel(t.status)}</span>`, timeAgo(t.updatedAt)];

    return `<tr data-row-id="${esc(t.id)}" class="${t.id===uiState.selectedTicketId?'is-selected':''}">
      ${cells.map(c => `<td>${typeof c === "string" && c.startsWith('<span') ? c : esc(String(c))}</td>`).join("")}
    </tr>`;
  }).join("");

  return `
    <div class="ticket-table-wrap">
      <table class="ticket-table">
        <thead><tr>${cols.map(c => `<th>${esc(c)}</th>`).join("")}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

// ── TICKET DETAIL ──────────────────────────────────────────────────
function renderTicketDetail() {
  const user = currentUser();
  const t = state.tickets.find(x => x.id === uiState.selectedTicketId);
  if (!t) {
    return `<div class="empty-state">
      <div class="empty-icon">👈</div>
      <div class="empty-msg">Pick a ticket to see details.</div>
    </div>`;
  }

  const team = getTeamById(state, t.assignedTeamId);
  const assignee = getUserById(state, t.assignedTo);
  const auth = getUserById(state, t.authorizedPersonId);
  const creator = getUserById(state, t.createdBy);
  const advanced = !isRequester(user);
  const tab = uiState.detailTab;

  const tabs = advanced ? ["Overview","Conversation","History"] : ["Overview","Conversation"];

  return `
    <div class="card">
      <div class="card-body">
        <div class="badge-row">
          <span class="badge">${esc(t.ticketNo)}</span>
          <span class="badge">${esc(t.system)} · ${esc(t.area)}</span>
          <span class="badge">${esc(t.priority)}</span>
          <span class="status-pill ${stClass(t.status)}">${esc(stLabel(t.status))}</span>
        </div>
        <h2 class="ticket-big-title">${esc(t.title)}</h2>
        <div class="small">From ${esc(creator?.name || '—')} · Created ${esc(fmt(t.createdAt, true))}</div>

        <div class="form-steps" style="margin-top:14px">
          ${tabs.map(x => `<div class="form-step ${tab===x?'is-active':''}" data-tab="${esc(x)}" style="cursor:pointer">${esc(x)}</div>`).join("")}
        </div>

        ${tab === "Overview" ? `
          <div class="meta-grid">
            <div class="meta-item"><span>Status</span>${esc(stLabel(t.status))}</div>
            <div class="meta-item"><span>Urgency</span>${esc(t.priority)}</div>
            <div class="meta-item"><span>Authorizer</span>${esc(auth?.name || '—')}</div>
            <div class="meta-item"><span>Team</span>${esc(team?.teamName || '—')}</div>
            <div class="meta-item"><span>Assigned To</span>${esc(assignee?.name || '—')}</div>
            <div class="meta-item"><span>Last Update</span>${esc(timeAgo(t.updatedAt))}</div>
            ${t.expectedDate ? `<div class="meta-item"><span>Expected Date</span>${esc(t.expectedDate)}</div>` : ""}
            ${advanced && t.attachmentNames?.length ? `<div class="meta-item"><span>Attachments</span>${t.attachmentNames.map(esc).join(", ")}</div>` : ""}
          </div>

          <div class="card" style="margin-top:14px">
            <div class="card-header"><span class="card-title">Description</span></div>
            <div class="card-body">${esc(t.description)}</div>
          </div>

          ${renderActionPanel(t, user)}
        ` : ""}

        ${tab === "Conversation" ? `
          ${renderNotesSection(t, user)}
        ` : ""}

        ${tab === "History" ? `
          ${renderHistorySection(t)}
        ` : ""}
      </div>
    </div>`;
}

function renderActionPanel(t, user) {
  const buttons = [];

  // Authorized Person
  if (canPerform(state, user, "approve", t) && t.status === "Pending Authorization") {
    const teamOpts = state.teams.filter(tm => tm.system === t.system && tm.isActive)
      .map(tm => `<option value="${esc(tm.id)}">${esc(tm.teamName)}</option>`).join("");
    return `
      <div class="card" style="margin-top:14px">
        <div class="card-header"><span class="card-title">Action — Approve / Send Back / Reject</span></div>
        <div class="card-body">
          <div class="field">
            <label>Route to team (on approve)</label>
            <select id="ap-team"><option value="">Select team…</option>${teamOpts}</select>
          </div>
          <div class="field">
            <label>Note (optional for approve, required for reject/send back)</label>
            <textarea id="ap-note" placeholder="Add reason or context"></textarea>
          </div>
          <div class="button-row">
            <button class="btn btn-primary" data-act="approve" data-id="${esc(t.id)}">Approve</button>
            <button class="btn btn-secondary" data-act="sendback" data-id="${esc(t.id)}">Send Back</button>
            <button class="btn btn-danger" data-act="reject" data-id="${esc(t.id)}">Reject</button>
          </div>
        </div>
      </div>`;
  }

  // Authorizer — close
  if (canPerform(state, user, "close", t) && t.status === "Completed") {
    return `
      <div class="card" style="margin-top:14px">
        <div class="card-header"><span class="card-title">Action — Verify and Close</span></div>
        <div class="card-body">
          <div class="field">
            <label>Closure note (optional)</label>
            <textarea id="ap-close-note" placeholder="Confirm verification details"></textarea>
          </div>
          <div class="button-row">
            <button class="btn btn-success" data-act="close" data-id="${esc(t.id)}">Close Ticket</button>
            <button class="btn btn-secondary" data-act="reopen" data-id="${esc(t.id)}">Reopen</button>
          </div>
        </div>
      </div>`;
  }

  // Team Lead — assign member
  if (canPerform(state, user, "assign-member", t) && ["Approved","Assigned to Team"].includes(t.status)) {
    const opts = getMemberOptions(t.assignedTeamId)
      .map(u => `<option value="${esc(u.id)}">${esc(u.name)}</option>`).join("");
    if (opts) {
      buttons.push(`
        <div class="card" style="margin-top:14px">
          <div class="card-header"><span class="card-title">Assign to Team Member</span></div>
          <div class="card-body">
            <div class="field">
              <label>Member</label>
              <select id="am-member"><option value="">Select member…</option>${opts}</select>
            </div>
            <div class="field"><label>Due Date</label><input id="am-due" type="date" value="${esc(t.dueDate||'')}" /></div>
            <div class="button-row">
              <button class="btn btn-primary" data-act="assign-member" data-id="${esc(t.id)}">Assign</button>
            </div>
          </div>
        </div>`);
    }
  }

  // Team — start work
  if (canPerform(state, user, "start-work", t) && ["Approved","Assigned to Team","On Hold","Reopened"].includes(t.status)) {
    buttons.push(`
      <div class="card" style="margin-top:14px">
        <div class="card-header"><span class="card-title">Start Work</span></div>
        <div class="card-body">
          <div class="field"><label>Note (optional)</label><textarea id="sw-note" placeholder="Plan or context"></textarea></div>
          <div class="button-row">
            <button class="btn btn-teal" data-act="start" data-id="${esc(t.id)}">Start Work</button>
          </div>
        </div>
      </div>`);
  }

  // Team — update / mark done
  if (canPerform(state, user, "update-work", t) && ["In Progress","Work Updated","Reopened"].includes(t.status)) {
    buttons.push(`
      <div class="card" style="margin-top:14px">
        <div class="card-header"><span class="card-title">Add Update / Mark Done</span></div>
        <div class="card-body">
          <div class="field"><label>Update note</label><textarea id="up-note" placeholder="What progress was made?"></textarea></div>
          <div class="button-row">
            <button class="btn btn-primary" data-act="update" data-id="${esc(t.id)}">Add Update</button>
            <button class="btn btn-secondary" data-act="hold" data-id="${esc(t.id)}">Put On Hold</button>
            <button class="btn btn-success" data-act="done" data-id="${esc(t.id)}">Mark Done</button>
          </div>
        </div>
      </div>`);
  }

  // Requester — reply / reopen
  if (isRequester(user) && t.createdBy === user.id) {
    if (t.status === "Need More Information") {
      buttons.push(`
        <div class="card" style="margin-top:14px">
          <div class="card-header"><span class="card-title">Reply</span></div>
          <div class="card-body">
            <div class="field"><label>Your reply</label><textarea id="rp-note" placeholder="Add the requested info"></textarea></div>
            <div class="button-row">
              <button class="btn btn-primary" data-act="reply" data-id="${esc(t.id)}">Send Reply</button>
            </div>
          </div>
        </div>`);
    }
    if (["Closed","Verified"].includes(t.status)) {
      buttons.push(`
        <div class="card" style="margin-top:14px">
          <div class="card-header"><span class="card-title">Reopen</span></div>
          <div class="card-body">
            <div class="field"><label>Why reopen?</label><textarea id="rop-note" placeholder="Reason for reopen (required)"></textarea></div>
            <div class="button-row">
              <button class="btn btn-secondary" data-act="reopen" data-id="${esc(t.id)}">Reopen</button>
            </div>
          </div>
        </div>`);
    }
  }

  return buttons.join("");
}

function renderNotesSection(t, user) {
  const notes = getVisibleNotes(t, user);
  const allowInternal = canPerform(state, user, "note-internal", t);

  const noteList = notes.length === 0
    ? `<div class="small">No conversation yet.</div>`
    : notes.map(n => `
        <div class="note-card">
          <div class="note-head">
            <strong>${esc(getUserById(state, n.createdBy)?.name || '—')}</strong>
            <span class="small">${esc(timeAgo(n.createdAt))} · ${esc(n.noteType)} · ${esc(n.visibility)}</span>
          </div>
          <div>${esc(n.noteText)}</div>
        </div>`).join("");

  return `
    <div class="card" style="margin-top:14px">
      <div class="card-header"><span class="card-title">Conversation</span></div>
      <div class="card-body">
        <div class="note-list">${noteList}</div>

        <div class="field">
          <label>Add a note</label>
          <textarea id="note-text" placeholder="Write a note…"></textarea>
        </div>
        <div class="field-grid">
          <div class="field">
            <label>Type</label>
            <select id="note-type">${renderOptions(NOTE_TYPES.filter(nt => allowInternal || nt !== "Internal Note"))}</select>
          </div>
          <div class="field">
            <label>Visibility</label>
            <select id="note-vis">
              <option value="Public">Public</option>
              ${allowInternal ? `<option value="Internal">Internal</option>` : ""}
            </select>
          </div>
        </div>
        <div class="button-row">
          <button class="btn btn-primary" data-act="add-note" data-id="${esc(t.id)}">Add Note</button>
        </div>
      </div>
    </div>`;
}

function renderHistorySection(t) {
  const hist = (state.statusHistory || []).filter(h => h.ticketId === t.id);
  const appr = (state.approvalHistory || []).filter(a => a.ticketId === t.id);
  return `
    <div class="card" style="margin-top:14px">
      <div class="card-header"><span class="card-title">Status History</span></div>
      <div class="card-body">
        <div class="timeline-list">
          ${hist.length === 0 ? `<div class="small">No status changes yet.</div>` :
            hist.map(h => `
              <div class="timeline-card">
                <div class="timeline-head">
                  <strong>${esc(stLabel(h.oldStatus))} → ${esc(stLabel(h.newStatus))}</strong>
                  <span class="small">${esc(fmt(h.changedAt, true))}</span>
                </div>
                <div class="small">By ${esc(getUserById(state, h.changedBy)?.name || '—')}</div>
                ${h.note ? `<div>${esc(h.note)}</div>` : ""}
              </div>`).join("")}
        </div>
      </div>
    </div>
    <div class="card" style="margin-top:14px">
      <div class="card-header"><span class="card-title">Approval Trail</span></div>
      <div class="card-body">
        <div class="timeline-list">
          ${appr.length === 0 ? `<div class="small">No approval action yet.</div>` :
            appr.map(a => `
              <div class="timeline-card">
                <div class="timeline-head">
                  <strong>${esc(a.action)}</strong>
                  <span class="small">${esc(fmt(a.actionAt, true))}</span>
                </div>
                <div class="small">By ${esc(getUserById(state, a.actionBy)?.name || '—')}</div>
                ${a.note ? `<div>${esc(a.note)}</div>` : ""}
              </div>`).join("")}
        </div>
      </div>
    </div>`;
}

// ── MODAL ──────────────────────────────────────────────────────────
function renderModal() {
  if (!uiState.modal) return "";
  const m = uiState.modal;
  return `
    <div class="modal-overlay is-open" id="modal-overlay">
      <div class="modal">
        <div class="modal-title">${esc(m.title)}</div>
        <div class="modal-body">${esc(m.body)}</div>
        ${m.requireReason ? `<div class="field"><label>Reason (required)</label><textarea id="modal-reason" placeholder="Enter reason"></textarea></div>`:""}
        <div class="modal-footer">
          <button class="btn btn-ghost" id="modal-cancel">Cancel</button>
          <button class="btn ${m.confirmStyle || 'btn-primary'}" id="modal-confirm">${esc(m.confirmLabel || 'Confirm')}</button>
        </div>
      </div>
    </div>`;
}

// ── MAIN RENDER ────────────────────────────────────────────────────
function render() {
  const user = currentUser();
  app.innerHTML = `
    ${renderNavbar()}
    <div class="app-shell">
      <main class="main-content">
        ${renderPageHeader()}
        ${renderStatCards()}
        ${(isAdminLike(user) || isAuthLike(user)) ? renderAdminPendingPanel() : ""}
        <div class="main-grid">
          <aside class="sidebar">
            ${renderCreateForm()}
          </aside>
          <section class="panel">
            <div class="panel-header">
              <span class="panel-title">${isRequester(user) ? "My Tickets" : isTeamLike(user) ? "My Work Queue" : "All Tickets"}</span>
              <span class="small">${getFiltered().length} shown</span>
            </div>
            ${renderFilters()}
            ${renderTicketTable()}
          </section>
        </div>
        <div class="detail-layout">
          <div>${renderTicketDetail()}</div>
        </div>
      </main>
    </div>
    ${renderModal()}
  `;
  bindEvents();
}

// ── EVENTS ─────────────────────────────────────────────────────────
function bindEvents() {
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => document.querySelectorAll(s);

  // Role switcher
  const roleSel = $("#role-select");
  if (roleSel) roleSel.onchange = (e) => {
    state.meta.currentUserId = e.target.value;
    uiState.selectedTicketId = "";
    uiState.activeChip = "All";
    persist().then(render);
  };

  // Notification bell
  const bell = $("#bell-btn");
  if (bell) bell.onclick = (e) => {
    e.stopPropagation();
    uiState.notifOpen = !uiState.notifOpen;
    render();
  };

  // Click outside to close notif
  if (uiState.notifOpen) {
    document.addEventListener("click", () => {
      uiState.notifOpen = false;
      render();
    }, { once: true });
  }

  $$(".notif-item").forEach(el => el.onclick = (e) => {
    e.stopPropagation();
    const id = el.dataset.notifId;
    const tid = el.dataset.ticketId;
    const n = state.notifications.find(x => x.id === id);
    if (n) n.isRead = true;
    if (tid) {
      uiState.selectedTicketId = tid;
      uiState.detailTab = "Overview";
    }
    uiState.notifOpen = false;
    persist().then(render);
  });

  const markAll = $("#notif-mark-all");
  if (markAll) markAll.onclick = (e) => {
    e.stopPropagation();
    state.notifications.forEach(n => n.isRead = true);
    persist().then(render);
    showToast("All notifications marked read");
  };

  const clrAll = $("#notif-clear-all");
  if (clrAll) clrAll.onclick = (e) => {
    e.stopPropagation();
    state.notifications = [];
    persist().then(render);
    showToast("Notifications cleared");
  };

  // Filter chips
  $$("[data-chip]").forEach(el => el.onclick = () => {
    uiState.activeChip = el.dataset.chip;
    uiState.selectedTicketId = "";
    render();
  });
  const fq = $("#filter-q");
  if (fq) fq.oninput = (e) => { uiState.filters.query = e.target.value; render(); fq.focus(); fq.setSelectionRange(fq.value.length, fq.value.length); };
  const fs = $("#filter-sys");
  if (fs) fs.onchange = (e) => { uiState.filters.system = e.target.value; render(); };
  const fc = $("#filter-clear");
  if (fc) fc.onclick = () => { uiState.filters = { query:"", status:"All", system:"All" }; uiState.activeChip="All"; render(); };
  const fr = $("#filter-reset");
  if (fr) fr.onclick = () => { uiState.filters = { query:"", status:"All", system:"All" }; uiState.activeChip="All"; render(); };

  // Ticket row select
  $$("[data-row-id]").forEach(el => el.onclick = () => {
    uiState.selectedTicketId = el.dataset.rowId;
    uiState.detailTab = "Overview";
    render();
  });

  // Detail tabs
  $$("[data-tab]").forEach(el => el.onclick = () => {
    uiState.detailTab = el.dataset.tab;
    render();
  });

  // ── CREATE FORM ──
  const sysSel = $("#cf-system");
  if (sysSel) sysSel.onchange = (e) => { uiState.createSystem = e.target.value; render(); };
  const cfNext1 = $("#cf-next-1");
  if (cfNext1) cfNext1.onclick = () => { uiState.createStep = 2; render(); };
  const cfBack2 = $("#cf-back-2");
  if (cfBack2) cfBack2.onclick = () => { uiState.createStep = 1; render(); };
  const cfNext2 = $("#cf-next-2");
  if (cfNext2) cfNext2.onclick = () => {
    const title = $("#cf-title")?.value.trim();
    const desc = $("#cf-desc")?.value.trim();
    if (!title) return showToast("Please enter title.", "error");
    if (!desc) return showToast("Please explain the issue.", "error");
    window.__cfDraft = {
      title, desc,
      attachment: $("#cf-attach")?.value.trim(),
      stone: $("#cf-stone")?.value.trim(),
      module: $("#cf-module")?.value.trim(),
      empcode: $("#cf-empcode")?.value.trim(),
      month: $("#cf-month")?.value.trim(),
      area: $("#cf-area")?.value.trim() || (AREA_OPTIONS[uiState.createSystem]||[])[0],
      issueType: $("#cf-issue-type")?.value.trim(),
    };
    uiState.createStep = 3; render();
  };
  const cfBack3 = $("#cf-back-3");
  if (cfBack3) cfBack3.onclick = () => { uiState.createStep = 2; render(); };
  $$("[data-urg]").forEach(el => el.onclick = () => { uiState.createUrgency = el.dataset.urg; render(); });
  $$("[data-template]").forEach(el => el.onclick = () => {
    const draft = window.__cfDraft || {};
    draft.title = el.dataset.template;
    window.__cfDraft = draft;
    uiState.createStep = 2; render();
    setTimeout(() => { const t = $("#cf-title"); if (t) t.value = draft.title; }, 0);
  });
  const cfSubmit = $("#cf-submit");
  if (cfSubmit) cfSubmit.onclick = async () => {
    const d = window.__cfDraft || {};
    const user = currentUser();
    if (!d.title) { showToast("Please enter title.", "error"); uiState.createStep = 2; return render(); }
    const issueToCategory = (it) => {
      if (!it) return "Bug";
      if (it.toLowerCase().includes("data")) return "Data Issue";
      if (it.toLowerCase().includes("new")) return "New Requirement";
      if (it.toLowerCase().includes("change")) return "Change Request";
      return "Bug";
    };
    const ticket = createTicket(state, user, {
      system: uiState.createSystem,
      area: d.area,
      category: issueToCategory(d.issueType),
      priority: uiState.createUrgency,
      title: d.title,
      description: [d.desc, d.stone && `Stone ID: ${d.stone}`, d.module && `Module: ${d.module}`, d.empcode && `Employee Code: ${d.empcode}`, d.month && `Month: ${d.month}`].filter(Boolean).join("\n"),
      attachmentName: d.attachment,
    });
    window.__cfDraft = null;
    uiState.createStep = 1;
    uiState.selectedTicketId = ticket.id;
    await persist();
    showToast("Ticket created successfully.");
    render();
  };

  // ── ADMIN PENDING QUICK ACTIONS ──
  $$("[data-act='approve-quick']").forEach(el => el.onclick = (e) => {
    e.stopPropagation();
    openApproveQuick(el.dataset.id);
  });
  $$("[data-act='sendback-quick']").forEach(el => el.onclick = (e) => {
    e.stopPropagation();
    openModal({
      title: "Send Back to User",
      body: "We will ask the user for more information. A reason is required.",
      requireReason: true,
      confirmLabel: "Send Back",
      confirmStyle: "btn-secondary",
      action: (reason) => {
        if (!reason) return showToast("Reason is required.", "error");
        const user = currentUser();
        requestMoreInformation(state, user, el.dataset.id, reason);
        persist().then(render);
        showToast("Ticket sent back to user.");
      }
    });
  });
  $$("[data-act='reject-quick']").forEach(el => el.onclick = (e) => {
    e.stopPropagation();
    openModal({
      title: "Reject Ticket",
      body: "Are you sure you want to reject this ticket? A reason is required.",
      requireReason: true,
      confirmLabel: "Reject",
      confirmStyle: "btn-danger",
      action: (reason) => {
        if (!reason) return showToast("Reason is required.", "error");
        const user = currentUser();
        rejectTicket(state, user, el.dataset.id, reason);
        persist().then(render);
        showToast("Ticket rejected.");
      }
    });
  });
  $$("[data-act='open-detail']").forEach(el => el.onclick = (e) => {
    e.stopPropagation();
    uiState.selectedTicketId = el.dataset.id;
    render();
  });

  // ── DETAIL ACTIONS ──
  bindDetailActions();

  // ── MODAL ──
  const cancel = $("#modal-cancel");
  if (cancel) cancel.onclick = () => { uiState.modal = null; render(); };
  const confirmBtn = $("#modal-confirm");
  if (confirmBtn) confirmBtn.onclick = () => {
    const reason = $("#modal-reason")?.value.trim() || "";
    const action = uiState.modal?.action;
    uiState.modal = null;
    if (typeof action === "function") action(reason);
    else render();
  };
}

function openApproveQuick(ticketId) {
  const t = state.tickets.find(x => x.id === ticketId);
  if (!t) return;
  const teams = state.teams.filter(tm => tm.system === t.system && tm.isActive);
  if (teams.length === 0) {
    const user = currentUser();
    approveTicket(state, user, ticketId, { note: "Approved." });
    persist().then(render);
    showToast("Ticket approved.");
    return;
  }
  const teamId = teams[0].id;
  const user = currentUser();
  approveTicket(state, user, ticketId, { note: "Approved.", teamId });
  persist().then(render);
  showToast(`Ticket approved and routed to ${teams[0].teamName}.`);
}

function bindDetailActions() {
  const $ = (s) => document.querySelector(s);
  const user = currentUser();

  document.querySelectorAll("[data-act='approve']").forEach(el => el.onclick = async () => {
    const note = $("#ap-note")?.value.trim() || "";
    const teamId = $("#ap-team")?.value || "";
    approveTicket(state, user, el.dataset.id, { note, teamId });
    await persist(); showToast("Ticket approved successfully."); render();
  });
  document.querySelectorAll("[data-act='sendback']").forEach(el => el.onclick = () => {
    const note = $("#ap-note")?.value.trim();
    if (!note) return showToast("Please add a reason.", "error");
    requestMoreInformation(state, user, el.dataset.id, note);
    persist().then(render); showToast("Sent back to user.");
  });
  document.querySelectorAll("[data-act='reject']").forEach(el => el.onclick = () => {
    const note = $("#ap-note")?.value.trim();
    if (!note) return showToast("Please add a reason.", "error");
    openModal({
      title: "Reject Ticket",
      body: "Are you sure you want to reject this ticket?",
      confirmLabel: "Reject",
      confirmStyle: "btn-danger",
      action: () => {
        rejectTicket(state, user, el.dataset.id, note);
        persist().then(render); showToast("Ticket rejected.");
      }
    });
  });
  document.querySelectorAll("[data-act='close']").forEach(el => el.onclick = () => {
    const note = $("#ap-close-note")?.value.trim() || "";
    openModal({
      title: "Close Ticket",
      body: "Are you sure this ticket is solved and can be closed?",
      confirmLabel: "Close Ticket",
      confirmStyle: "btn-success",
      action: () => {
        verifyAndCloseTicket(state, user, el.dataset.id, note);
        persist().then(render); showToast("Ticket closed.");
      }
    });
  });
  document.querySelectorAll("[data-act='reopen']").forEach(el => el.onclick = () => {
    const note = ($("#ap-close-note")?.value || $("#rop-note")?.value || "").trim();
    if (!note) return showToast("Please add a reason for reopen.", "error");
    openModal({
      title: "Reopen Ticket",
      body: "Are you sure you want to reopen this ticket?",
      confirmLabel: "Reopen",
      confirmStyle: "btn-secondary",
      action: () => {
        reopenTicket(state, user, el.dataset.id, note);
        persist().then(render); showToast("Ticket reopened.");
      }
    });
  });
  document.querySelectorAll("[data-act='assign-member']").forEach(el => el.onclick = () => {
    const memberId = $("#am-member")?.value;
    const due = $("#am-due")?.value || "";
    if (!memberId) return showToast("Please select a member.", "error");
    assignMember(state, user, el.dataset.id, memberId, due, "");
    persist().then(render); showToast("Assigned to team member.");
  });
  document.querySelectorAll("[data-act='start']").forEach(el => el.onclick = () => {
    const note = $("#sw-note")?.value.trim() || "Work started.";
    startWork(state, user, el.dataset.id, note);
    persist().then(render); showToast("Work started.");
  });
  document.querySelectorAll("[data-act='update']").forEach(el => el.onclick = () => {
    const note = $("#up-note")?.value.trim();
    if (!note) return showToast("Please add an update note.", "error");
    updateWork(state, user, el.dataset.id, { note, status: "Work Updated", noteType: "Work Note", visibility: VISIBILITY.PUBLIC });
    persist().then(render); showToast("Work update added.");
  });
  document.querySelectorAll("[data-act='hold']").forEach(el => el.onclick = () => {
    const note = $("#up-note")?.value.trim() || "Put on hold.";
    updateWork(state, user, el.dataset.id, { note, status: "On Hold", noteType: "Work Note", visibility: VISIBILITY.PUBLIC });
    persist().then(render); showToast("Ticket put on hold.");
  });
  document.querySelectorAll("[data-act='done']").forEach(el => el.onclick = () => {
    const note = $("#up-note")?.value.trim();
    if (!note) return showToast("Please add a resolution note.", "error");
    completeTicket(state, user, el.dataset.id, { resolutionNote: note, rootCause: "" });
    persist().then(render); showToast("Marked as done.");
  });
  document.querySelectorAll("[data-act='reply']").forEach(el => el.onclick = () => {
    const note = $("#rp-note")?.value.trim();
    if (!note) return showToast("Please write your reply.", "error");
    appendGeneralNote(state, user, el.dataset.id, { noteType: "User Comment", noteText: note, visibility: VISIBILITY.PUBLIC });
    persist().then(render); showToast("Reply sent.");
  });
  document.querySelectorAll("[data-act='add-note']").forEach(el => el.onclick = () => {
    const text = $("#note-text")?.value.trim();
    if (!text) return showToast("Please write a note.", "error");
    const noteType = $("#note-type")?.value || "User Comment";
    const visibility = $("#note-vis")?.value || "Public";
    appendGeneralNote(state, user, el.dataset.id, { noteType, noteText: text, visibility });
    persist().then(render); showToast("Note added.");
  });
}

function openModal(m) { uiState.modal = m; render(); }

// ── BOOT ──────────────────────────────────────────────────────────
async function boot() {
  await loadOptionalRuntimeConfig();
  config = getAppConfig();
  const local = createLocalAdapter();
  adapter = config.firebase?.enabled
    ? await createFirebaseAdapter(config, local)
    : local;
  const seed = createSeedState();
  let loaded;
  try { loaded = await adapter.load(seed); }
  catch (e) { console.warn("load failed, using seed", e); loaded = seed; }
  state = normalizeStateShape(loaded);
  if (!state.meta.currentUserId) state.meta.currentUserId = state.users[0]?.id;
  render();
  if (adapter.warning) showToast(adapter.warning, "error");
}

boot();
