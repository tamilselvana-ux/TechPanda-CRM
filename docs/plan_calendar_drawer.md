# DigiPanda CRM — Responsive Calendar Drawer Implementation Plan (Phase 2)

**Document:** `docs/plan_calendar_drawer.md`  
**Date:** October 30, 2026  
**Authors:** 03a Project Manager, 04 Software Architect (CTO), 06 Tech Lead, 05 UI/UX Design Team  
**Status:** **AWAITING FOUNDER APPROVAL (APPROVAL GATE)**  

---

## 1. Executive Summary & Goals

The objective is to replace the fragmented, anchored floating date popovers across the CRM with **ONE shared, premium, responsive Calendar Drawer** loaded once in the global application shell ([`templates/base.html`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/templates/base.html)).

The Calendar Drawer eliminates viewport clipping, table container overflow bugs, mobile touch inaccessibility, and z-index clashes, while preserving 100% of existing backend query parameter names, inclusive end-date filtering, and timezone handling (`Asia/Kolkata`).

---

## 2. Component Architecture

```
                                  base.html
                                      │
          ┌───────────────────────────┴───────────────────────────┐
          ▼                                                       ▼
templates/components/calendar_drawer.html             static/js/calendar-drawer.js
(Single DOM element in body, z-index: 99999)          (Universal Singleton Controller)
          ▲                                                       │
          │ binds dynamically                                     │ opens & renders
          └───────────────────────────────────────────────────────┘
                                      ▲
                         Trigger: .calendar-drawer-trigger
                      (on any of the 17 date-filtered pages)
```

### 2.1 File Inventory

| File Path | Role | Responsibility |
|---|---|---|
| [`templates/components/calendar_drawer.html`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/templates/components/calendar_drawer.html) | Django Partial / Include | Single modal drawer DOM markup with backdrop, header, preset pills, dual/single calendar grid, manual inputs, and sticky footer. |
| [`static/css/calendar-drawer.css`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/static/css/calendar-drawer.css) | Scoped Stylesheet | Pure CSS styling using design system tokens (`--tp-surface-*`, `--tp-text-*`), fluid responsive drawer breakpoints, and smooth motion transitions. |
| [`static/js/calendar-drawer.js`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/static/js/calendar-drawer.js) | Vanilla JS Module | Zero-dependency singleton controller. Binds to `.calendar-drawer-trigger`, extracts active page inputs, manages calendar state, renders grid, validates, and submits form. |
| [`templates/base.html`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/templates/base.html) | Global Layout Shell | Includes `calendar_drawer.html`, `calendar-drawer.css`, and `calendar-drawer.js` once for all authenticated views. |

---

## 3. Responsive UI / UX Specification

### 3.1 Breakpoint Behaviors

| Viewport Category | Width | Drawer Layout & Behavior | Calendar Display |
|---|---|---|---|
| **Desktop** | $\ge 900\text{px}$ | Right-side slide-over drawer ($720\text{px}$ wide). Ambient backdrop blur (`backdrop-filter: blur(4px)`). Body scroll locked. | **Two months side-by-side** (Current + Next, or Previous + Current). |
| **Tablet** | $600\text{px} - 899\text{px}$ | Right-side slide-over drawer ($90\text{vw}$ wide). Responsive layout. | Adaptive (Two months on landscape, One month on portrait). |
| **Phone** | $< 600\text{px}$ | **Bottom-sheet drawer** sliding up from bottom ($100\text{vw}$, max-height $92\text{vh}$). Rounded top corners ($24\text{px}$). | **Single month view**. Minimum touch target $\mathbf{\ge 44\times44\text{px}}$. Sticky Apply footer always pinned. |

### 3.2 Visual & Range States

- **Preset Bar:** `Today`, `Yesterday`, `Last 7 Days`, `Last 30 Days`, `This Month`, `Last Month`, `This FY`, `Custom Range`. Active preset is highlighted with primary blue badge.
- **Range Selection:**
  - Start Date: Left pill boundary / blue solid circle with white bold text (`#0a53b5`).
  - End Date: Right pill boundary / blue solid circle with white bold text (`#0a53b5`).
  - Dates In-Between: Soft tint background (`rgba(10, 83, 181, 0.08)` in light, `rgba(10, 83, 181, 0.22)` in dark) with seamless connected pill edges.
  - Today Indicator: Underline or small blue dot below the day number.
  - Hover Preview: Retained DOM hover range preview before final selection click.
- **Manual Date Inputs:** Dual inputs for Start Date and End Date at top of drawer. Typing updates the calendar selection in real time.
- **Sticky Footer:**
  - **Clear:** Empties date parameters (matches existing "Clear" behavior).
  - **Cancel / Close:** Discards changes and restores previously committed range.
  - **Apply:** Validates, commits dates, updates trigger label, and submits the target form.

### 3.3 Motion Specification

- **Drawer Entrance:** Slide from right (or bottom on mobile) using `transform: translateX(100%)` $\to$ `transform: translateX(0)` in **$220\text{ms}$** with easing `cubic-bezier(0.16, 1, 0.3, 1)`.
- **Backdrop Fade:** `opacity: 0` $\to$ `opacity: 1` in $200\text{ms}$.
- **Reduced Motion:** If `@media (prefers-reduced-motion: reduce)`, transitions instantaneously without motion (`transition: none !important; opacity: 1 !important; transform: none !important;`).

### 3.4 Accessibility (a11y) & Focus Management

- `role="dialog"`, `aria-modal="true"`, `aria-labelledby="calendar-drawer-title"`.
- Focus trap inside the drawer while open (`Tab` / `Shift+Tab` cycles inside drawer).
- Opening moves focus to the first interactive element (preset button or start input).
- Closing returns focus directly to the `.calendar-drawer-trigger` button that invoked it.
- Keyboard navigation: Arrow keys navigate between calendar days; `Enter` selects a date; `Escape` closes the drawer.

---

## 4. Date Parameter & Backend Compatibility Rules

To ensure **zero regressions** on existing bookmarks, saved links, pagination, and Excel exports:

1. **Parameter Name Preservation:**
   - The drawer dynamically inspects the host form for input names:
     - On listing pages using `date_from` / `date_to`: assigns `date_from` and `date_to`.
     - On dashboard pages using `start_date` / `end_date`: assigns `start_date` and `end_date`.
     - On accountant views using `from` / `to`: assigns `from` and `to`.
     - If `period` exists: sets the active preset slug or `'custom'`.
2. **Inclusive End-Date:**
   - Dates are formatted strictly as `YYYY-MM-DD`.
   - The backend utility ([`CRM/leads/utils_date_filter.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/leads/utils_date_filter.py)) makes the end date inclusive through `23:59:59.999999` in `Asia/Kolkata`.
3. **Form Submission & Pagination Reset:**
   - When Apply is clicked, the drawer resets any pagination parameter (`page=1` or deletes `page`) while preserving all other active filters (search query `q`, `status`, `branch`, `counselor`, `telecaller`).
4. **Validation:**
   - If `start_date > end_date` is entered: inline error message displays *"Start date cannot be after End date"*, and the Apply button is disabled.

---

## 5. Regression Test Matrix (Page × Check)

| Page Route | Item # | Drawer Opens & Focus Traps | Preset Selection | Two-Month Desktop | Single-Month Mobile 390px | Form Submission | Page 1 Reset | Export Respects Range | Both Themes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `/admin/dashboard/` | 01 | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | N/A | [ ] |
| `/accountant/dashboard/` | 02 | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | [ ] | [ ] |
| `/accountant/verification/` | 03 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | [ ] |
| `/admin/leads/` | 04 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| `/admin/leads/new/` | 05 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | [ ] |
| `/branch-head/dashboard/` | 06 | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | N/A | [ ] |
| `/counselor/dashboard/` | 07 | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | N/A | [ ] |
| `/manager/dashboard/` | 08 | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | N/A | [ ] |
| `/telecaller/dashboard/` | 09 | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | N/A | [ ] |
| `/admin/calls/` | 10 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | [ ] |
| `/calls/recordings/` | 11 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | [ ] |
| `/admin/followups/` | 12 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | [ ] |
| `/counselor/followups/` | 13 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | [ ] |
| `/reports/` | 14 | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | [ ] | [ ] |
| `/reports/dashboard-report/` | 15 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| `/reports/telecaller-rnr/` | 16 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| `/finance/dashboard/` | 17 | [ ] | [ ] | [ ] | [ ] | [ ] | N/A | N/A | [ ] |

---

## 6. Risk Management & Rollback Strategy

- **Risk:** Existing native date inputs on third-party scripts or custom forms failing to serialize.
  - *Mitigation:* The drawer does not delete the host form's `<input type="hidden">` or `<input type="date">` tags. It updates their `.value` and triggers standard `'change'` and `'input'` DOM events before submitting.
- **Risk:** Stacking context clipping by parent elements.
  - *Mitigation:* `calendar_drawer.html` is attached directly as a child of `<body>` in `base.html` with fixed positioning and `z-index: 99999`, completely immune to parent container clipping or table overflows.
- **Rollback:**
  - The drawer is completely modular. Removing the include in `base.html` and restoring original buttons immediately reverts the UI with zero database or backend alterations.
