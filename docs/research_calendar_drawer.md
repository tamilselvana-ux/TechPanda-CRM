# DigiPanda CRM — Calendar Drawer Research & Usability Audit (Phase 1)

**Document:** `docs/research_calendar_drawer.md`  
**Date:** October 30, 2026  
**Auditor:** 12 Codebase Analyst & 05a UX Researcher  
**Status:** Complete  

---

## 1. Inventory of Every Page with a Date Filter

The CRM codebase was audited across all templates, URL routes, views, and JavaScript handlers. Below is the comprehensive mapping of all **17 date-filtered views and listing pages**:

| Item # | Page Title & Route | Template Path | View Function & File | Active Query Params | Queryset Filtering Mechanism | Timezone & End-Date Behavior | KPIs, Pagination & Exports |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | **Admin Dashboard**<br>`/admin/dashboard/` | `templates/admin_dashboard/dashboard.html` | `leads.views.admin_dashboard`<br>([`CRM/leads/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/leads/views.py)) | `from_date`, `to_date`<br>(also `start_date`, `end_date`, `period`) | Normalizes via `extract_normalized_date_range`. Filters `Lead.objects.filter(created_at__range=(start_dt, end_dt))` for all metrics. | `Asia/Kolkata`<br>**Inclusive** (`23:59:59.999999`) | All 8 KPI cards, counselor breakdown, and source charts strictly use the date range. |
| **02** | **Accountant Dashboard**<br>`/accountant/dashboard/` | `templates/accountant/dashboard.html` | `leads.views_accountant.accountant_dashboard`<br>([`CRM/leads/views_accountant.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/leads/views_accountant.py)) | `from`, `to`, `start_date`, `end_date`, `period` | Normalizes via `extract_normalized_date_range`. Filters `PaymentTransaction.objects.filter(payment_date__range=(start_dt, end_dt))`. | `Asia/Kolkata`<br>**Inclusive** (`23:59:59`) | Header range label, KPI tiles, and pending payment queue filter by range. |
| **03** | **Accountant Verification Queue**<br>`/accountant/verification/` | `templates/accountant/verification_list.html` | `leads.views_accountant.accountant_payment_verification`<br>([`CRM/leads/views_accountant.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/leads/views_accountant.py)) | `start_date`, `end_date` | Filters transactions awaiting verification: `payment_date__range=(start_dt, end_dt)`. | `Asia/Kolkata`<br>**Inclusive** | Pagination preserves `start_date` and `end_date`. |
| **04** | **Admin Leads Listing**<br>`/admin/leads/` | `templates/admin/leads_list.html` | `leads.views.admin_leads_list`<br>([`CRM/leads/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/leads/views.py)) | `date_from`, `date_to`<br>(also `start_date`, `end_date`) | Filters `Lead.objects.filter(created_at__range=(start_dt, end_dt))`. Preserves search and branch. | `Asia/Kolkata`<br>**Inclusive** | Pagination and Excel export preserve `date_from`/`date_to`. |
| **05** | **Admin New Leads Queue**<br>`/admin/leads/new/` | `templates/admin/new_leads_list.html` | `leads.views.admin_new_leads`<br>([`CRM/leads/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/leads/views.py)) | `date_from`, `date_to` | Filters unassigned/new leads: `status='New'`, `created_at__range=(start_dt, end_dt)`. | `Asia/Kolkata`<br>**Inclusive** | Pagination retains date filters. |
| **06** | **Branch Head Dashboard**<br>`/branch-head/dashboard/` | `templates/branch_head_dashboard/dashboard.html` | `branch_heads.views.branch_head_dashboard`<br>([`CRM/branch_heads/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/branch_heads/views.py)) | `period`, `start_date`, `end_date` | Normalizes via `extract_normalized_date_range`. Scoped to branch leads: `created_at__range=(start_dt, end_dt)`. | `Asia/Kolkata`<br>**Inclusive** | Branch KPIs, counselor lead tallies, and charts filter by range. |
| **07** | **Counselor Dashboard**<br>`/counselor/dashboard/` | `templates/counselor_dashboard/dashboard.html` | `counselors.views.counselor_dashboard`<br>([`CRM/counselors/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/counselors/views.py)) | `period`, `start_date`, `end_date` | Normalizes via `extract_normalized_date_range`. Scoped to assigned counselor: `created_at__range=(start_dt, end_dt)`. | `Asia/Kolkata`<br>**Inclusive** | Personal counselor KPI summary tiles update with range. |
| **08** | **Sales Head Dashboard**<br>`/manager/dashboard/` | `templates/manager_dashboard/dashboard.html` | `managers.views.manager_dashboard`<br>([`CRM/managers/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/managers/views.py)) | `period`, `start_date`, `end_date` | Normalizes via `extract_normalized_date_range`. Scoped to managed branches/counselors. | `Asia/Kolkata`<br>**Inclusive** | Sales velocity KPIs and team performance respect range. |
| **09** | **Telecaller Dashboard**<br>`/telecaller/dashboard/` | `templates/telecaller_dashboard/dashboard.html` | `telecallers.views.telecaller_dashboard`<br>([`CRM/telecallers/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/telecallers/views.py)) | `period`, `start_date`, `end_date` | Normalizes via `extract_normalized_date_range`. Scoped to assigned telecaller. | `Asia/Kolkata`<br>**Inclusive** | Daily call targets and reachability metrics update with range. |
| **10** | **Admin Calls Listing**<br>`/admin/calls/` | `templates/admin/calls_list.html` | `calls.views.calls_list`<br>([`CRM/calls/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/calls/views.py)) | `date_from`, `date_to` | Filters call logs: `call_start_time__range=(start_dt, end_dt)`. | `Asia/Kolkata`<br>**Inclusive** | Pagination and duration totals preserve range. |
| **11** | **Call Recordings Listing**<br>`/calls/recordings/` | `templates/calls/recordings_list.html` | `calls.views.recordings_list`<br>([`CRM/calls/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/calls/views.py)) | `date_from`, `date_to` | Filters audio recordings: `created_at__range=(start_dt, end_dt)`. | `Asia/Kolkata`<br>**Inclusive** | Pagination and player queue preserve range. |
| **12** | **Admin Follow-ups Listing**<br>`/admin/followups/` | `templates/admin/followups_list.html` | `followups.views.followups_list`<br>([`CRM/followups/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/followups/views.py)) | `date_from`, `date_to` | Filters scheduled follow-ups: `scheduled_date__range=(start_date, end_date)`. | `Asia/Kolkata`<br>**Inclusive** | Status filter, telecaller filter, and pagination preserve range. |
| **13** | **Counselor Follow-ups Listing**<br>`/counselor/followups/` | `templates/counselor/followups_list.html` | `followups.views.counselor_followups_list`<br>([`CRM/followups/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/followups/views.py)) | `date_from`, `date_to` | Filters counselor's scheduled calls: `scheduled_date__range`. | `Asia/Kolkata`<br>**Inclusive** | Pagination retains range. |
| **14** | **Analytics & Performance Reports**<br>`/reports/` | `templates/reports/admin_reports.html` | `reports.views.admin_reports`<br>([`CRM/reports/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/reports/views.py)) | `date_from`, `date_to` | Filters comprehensive lead conversion funnels and revenue stats. | `Asia/Kolkata`<br>**Inclusive** | Charts and aggregate KPI tables strictly use range. |
| **15** | **Marketing & Performance Report**<br>`/reports/dashboard-report/` | `templates/reports/dashboard_report.html` | `reports.views.dashboard_report`<br>([`CRM/reports/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/reports/views.py)) | `start_date`, `end_date`, `period` | Normalizes via `extract_normalized_date_range`. Generates channel conversion breakdown. | `Asia/Kolkata`<br>**Inclusive** | Channel performance table and export respect range. |
| **16** | **Telecaller RNR Report**<br>`/reports/telecaller-rnr/` | `templates/reports/telecaller_rnr_report.html` | `reports.views.telecaller_rnr_report`<br>([`CRM/reports/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/reports/views.py)) | `period`, `start_date`, `end_date` | Normalizes via `extract_normalized_date_range`. Computes Ring-No-Response rates. | `Asia/Kolkata`<br>**Inclusive** | Telecaller call breakdown and export respect range. |
| **17** | **Finance Dashboard & Oversight**<br>`/finance/dashboard/` & `/finance/oversight/` | `templates/finance/dashboard.html` | `finance.views.finance_dashboard`<br>([`CRM/finance/views.py`](file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/finance/views.py)) | `period` | Filters ledger transactions and branch collection totals. | `Asia/Kolkata`<br>**Inclusive** | Branch financial tiles filter by period. |

---

## 2. Technical Findings: Timezone, Inclusive Dates, and Theming

1. **Inclusive End-Date Behavior:**
   - Handled via `CRM/leads/utils_date_filter.py`:
     ```python
     end_dt = timezone.make_aware(datetime.combine(end_date_obj, time.max)) # 23:59:59.999999
     ```
   - When users select an end date (e.g. `2026-10-30`), all records created or paid up through `2026-10-30 23:59:59` in timezone `Asia/Kolkata` are included.
2. **Current Theming System:**
   - **Storage:** `localStorage.getItem('techpanda_theme')` and `localStorage.getItem('digipanda_theme')` (`'dark'` or `'light'`).
   - **DOM Representation:** `document.documentElement.setAttribute('data-theme', theme)` and `document.body.className = theme + '-theme'`.
   - **Core Design Tokens:**
     - Surface background: `var(--tp-surface-bg, #f8fafc)` (light) / `var(--tp-surface-bg, #0f172a)` (dark).
     - Surface cards: `var(--tp-surface-card, #ffffff)` (light) / `var(--tp-surface-card, #1e293b)` (dark).
     - Text colors: `var(--tp-text-primary, #0f172a)` / `var(--tp-text-secondary, #475569)` / `var(--tp-text-muted, #94a3b8)`.
     - Brand accents: Royal Blue `#0a53b5` / Emerald Green `#2bb34b`.
3. **Existing Date Picker Libraries:**
   - Zero third-party external dependencies (no jQuery UI, Flatpickr, DateRangePicker, or Moment.js).
   - Base template currently loads `static/js/smart-calendar.js`, which renders an anchored floating dropdown popover.

---

## 3. Real Problems Identified with Existing Floating Popover

Screenshots were captured at **1366px (Desktop)** and **390px (Mobile)** across both **Light** and **Dark** themes (saved to `docs/qa/calendar_baseline/`):

1. **Mobile Viewport Overflow (390px):**
   - The current floating popover has a fixed width ($\approx 640\text{px}$) designed for dual-month layout. On a 390px mobile viewport, the popover overflows 250px off-screen to the right, causing horizontal page break and cutting off the second month and action buttons.
2. **Table Container Z-Index & Overflow Clipping:**
   - On data table listing pages (e.g. `/admin/leads/`, `/admin/calls/`), parent card containers often have `overflow-x: auto` for responsive tables. When an anchored popover exceeds the card boundary, it gets clipped or triggers unwanted horizontal scrollbars inside the filter bar.
3. **Touch Inaccessibility:**
   - Date cells in the floating popover are $28\times28\text{px}$, well below the WCAG 2.2 AA target size ($44\times44\text{px}$ minimum for mobile touch).
4. **Lack of Background Scroll Lock:**
   - Opening the popover on mobile does not lock `body` scrolling; dragging to pick dates accidentally scrolls the dashboard behind the picker.
5. **Inconsistent Component Instances:**
   - Several pages (e.g. `/accountant/dashboard/`) developed separate bespoke date pickers with different HTML structures rather than sharing a single global component.

---

## 4. The Calendar Drawer Solution

Transitioning from an anchored floating popover to a **Responsive Calendar Drawer** provides:
- **Desktop ($\ge 900$px):** A sleek, full-height slide-over drawer on the right edge ($720\text{px}$ wide) with an ambient frosted backdrop (`z-index: 99999`), dual-month calendar, quick presets bar, start/end inputs, and a sticky footer.
- **Tablet ($600\text{–}899$px):** Responsive $90\text{vw}$ slide-out drawer.
- **Mobile ($< 600$px):** Bottom-sheet drawer with a **single month view**, touch cells $\ge 44\text{px}$, sticky action footer always visible, and background scroll locking (`body.drawer-open`).
- **Unified Global Component:** One Django partial included in `base.html`, loaded once, triggered by any `.calendar-drawer-trigger` on any page.
