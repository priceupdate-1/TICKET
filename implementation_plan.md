# Phase 3 — Full UI Overhaul + Firebase Fix + Admin Dashboard

## Summary

Two major problems to fix + one complete design overhaul:

1. **Firebase not saving** — `.env` has `FIREBASE_ENABLED=false`. There is no `app.config.js` file (only `app.config.example.js`). The config system reads `window.__APP_CONFIG__` from a runtime script file. Firebase is never enabled.
2. **UI too complex for non-technical users** — As documented in `phase3.md`.
3. **Admin dashboard simplification** — Admin should see pending tickets + notifications directly on the dashboard.

---

## Root Cause: Why Firebase is NOT Working

> [!CAUTION]
> The `.env` file has `FIREBASE_ENABLED=false`. But more critically — there is no `app.config.js` file at all. The app loads `app.config.js` at runtime via a `<script>` tag, and that file must set `window.__APP_CONFIG__`. Without it, the app always falls back to local browser storage.

**Fix:** Create `app.config.js` (from the example) with `firebase.enabled: true` and the real Firebase credentials already present in `.env`.

---

## Proposed Changes

### 1. Firebase Fix

#### [NEW] `app.config.js`
Generate this file (currently missing) with `window.__APP_CONFIG__` pointing to the real Firebase project `kg-ticket` with `enabled: true`.

---

### 2. Complete UI Overhaul (`styles.css`)

Full redesign based on `skill.md` + `skill1.md` directives:
- **Dark mode** — Deep graphite/slate palette (`#0f1117`, `#1a1f2e`)
- **Accent color** — Vibrant amber/gold `#f59e0b` for CTAs
- **Brand color** — Deep teal `#0d9488`
- **Typography** — Outfit (Google Font) for headings, Inter for body
- **Glassmorphism** — Cards with `backdrop-filter: blur` on dark surfaces
- **Micro-animations** — Button hover lifts, card hover scale, status pill transitions
- **Notification bell** — Floating badge in topbar header
- **Toast messages** — Slide-in confirmation toasts after every action
- **Role-based home cards** — Different quick-stat cards per role
- **Empty state designs** — Illustrated empty states with action buttons
- **Quick filter chips** — All / Open / Need My Action / Urgent / Closed

---

### 3. New Admin Dashboard Layout (`src/main.js`)

Admin dashboard shows:
- **Pending tickets directly** (no need to open detail) — inline quick action (Approve / Send Back / Reject) right on the dashboard card
- **Notification panel** moved to be prominent, shows unread count badge
- **Simplified stat cards** — Total / Pending Approval / In Progress / Closed Today
- **Role-based home page** — Different layout/cards for: Request User, Authorized Person, Team, Admin

---

### 4. UX Simplification per `phase3.md`

- **3-step create form** — Step 1: System + Issue Type, Step 2: Title + Description, Step 3: Urgency
- **User-friendly status labels** — "Waiting for Approval" instead of "Pending Authorization"
- **Role-based button visibility** — Only show buttons relevant to the current user's role
- **Notification bell** in the top header with unread count, clickable dropdown
- **Toast messages** after every action (success/error)
- **Confirmation modals** for Reject, Close, Reopen actions
- **Smart contextual fields** — Lattice-specific vs Trybe-specific optional fields
- **Quick filter chips** in ticket list
- **Simple vs Advanced view** — Regular users see simplified ticket detail; admins see full audit history

---

### Files to Modify

| File | Change |
|------|--------|
| `app.config.js` | **[NEW]** Enable Firebase with real credentials |
| `styles.css` | **Full overwrite** — Dark premium design system |
| `src/main.js` | **Major rewrite** — Role-based UX, admin dashboard, notifications, toasts |
| `index.html` | Update Google Fonts (add Outfit + Inter) |
| `src/data.js` | Add `isRead` to notifications, add `urgency` friendly label mapping |

---

## Verification Plan

### Automated
- Open the app in browser after changes
- Switch between all roles (Admin, Authorized Person, Request User, Team)
- Create a ticket, verify it saves to Firebase (check Firebase console)
- Verify notification bell shows count
- Verify toast appears after actions

### Manual Verification
- Admin dashboard shows pending tickets + inline approve button
- Notification badge shows unread count
- UI looks dark, premium, and modern (not the old beige/cream look)
- Firebase stores data (mode badge shows "Firebase Sync")

---

## Open Questions

> [!IMPORTANT]
> **Firebase credentials are already in `.env` but `.env` is not read by browser apps directly.** The fix is to create `app.config.js` which hardcodes (or is generated from) the values. Since this is a client-side app with public Firebase keys, this is acceptable for this project scope.

> [!NOTE]
> The existing data model stores all state as a **single Firestore document** (`primary_state` in collection `ticket_system`). This works fine for demo/small scale. For production with many concurrent users, this would need a per-ticket document approach. For now, keeping the same approach.
