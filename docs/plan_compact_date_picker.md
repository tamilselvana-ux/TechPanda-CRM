# DigiPanda CRM — Compact Date Range Picker Implementation Plan

## 1. Executive Summary & Objective

In accordance with Founder instructions, the existing custom date filters across the DigiPanda CRM are being replaced with **ONE shared, ready-made compact pop-up calendar component** (`static/js/date-range-picker.js` and `static/css/date-range-picker.css`).

### UX Specifications
- **Trigger**: An inline trigger input field (`≈280px` or full width on mobile) showing `"Select date range"` or formatted range `"10 Oct 2026 – 18 Oct 2026"`.
- **Calendar**: Single compact month popup (`≈280px`).
- **Interaction**:
  - **Click 1**: Selects the **From** (start) date.
  - **Click 2**: Selects the **To** (end) date (handles reverse order clicks automatically).
  - **Auto-apply**: Immediately sets hidden inputs, closes the pop-up, and auto-submits the form (`data-autosubmit="true"`).
  - **Cancel/Escape**: Pressing Escape or clicking outside cancels an incomplete selection and restores previous values without submitting.
  - **Clear Link**: Small link inside the footer resets the date filter to empty and submits.
- **Zero Dependencies**: Pure vanilla JavaScript, zero external libraries.

---

## 2. Complete Inventory of Affected Pages (18 Pages Audited)

| # | Page / Feature | URL Route | Template | Backend View | From Param | To Param | Preset / Period Param | End-Date Handling | Other Filters & Features |
|---|---|---|---|---|---|---|---|---|---|
| **1** | Admin Executive Dashboard | `/admin/dashboard/` | `templates/admin_dashboard/dashboard.html` | `reports.views.admin_dashboard` | `from_date` | `to_date` | None | `23:59:59.999999` (Inclusive) | Branch, counselor, telecaller, source, product. KPIs recalculate. |
| **2** | Accountant Financial Dashboard | `/accountant/dashboard/` | `templates/accountant/dashboard.html` | `leads.views_accountant.accountant_dashboard` | `start_date` | `end_date` | None (defaults to month) | `23:59:59.999999` (Inclusive) | Branch scope. 6 financial metric cards calculate for active window. |
| **3** | Accountant Verification Queue | `/accountant/verification/` | `templates/accountant/verification_list.html` | `leads.views_accountant.accountant_payment_verification` | `start_date` | `end_date` | None | `time.max` (Inclusive) | Status (`PENDING_VERIFICATION`, `APPROVED`, etc.), method, counselor, branch, search query `q`. Paginated. |
| **4** | Admin Leads Listing | `/admin/leads/` | `templates/admin/leads_list.html` | `leads.views.admin_leads_list` | `date_from` | `date_to` | None | `23:59:59.999999` (Inclusive) | Search `q`, status, stage, rating, channel, product, branch, telecaller, counselor, sort. Paginated. |
| **5** | Admin New Leads Queue | `/admin/leads/new/` | `templates/admin/new_leads_list.html` | `leads.views.admin_new_leads` | `date_from` | `date_to` | None | `23:59:59.999999` (Inclusive) | Search `q`, branch, telecaller, counselor, category, source, sort. Paginated. |
| **6** | Branch Head Dashboard | `/manager/branch-head/dashboard/` | `templates/branch_head_dashboard/dashboard.html` | `branch_heads.views.branch_head_dashboard` | `start_date` | `end_date` | `period=custom` | `23:59:59.999999` (Inclusive) | Branch-scoped KPIs: conversion rate, footfall, counselor distribution, revenue. |
| **7** | Counselor Dashboard | `/counselor/dashboard/` | `templates/counselor_dashboard/dashboard.html` | `counselors.views.counselor_dashboard` | `start_date` | `end_date` | `period=custom` | `23:59:59.999999` (Inclusive) | Counselor-scoped KPIs: conversion rate, walk-ins met, followups scheduled/completed. |
| **8** | Sales Head / Manager Dashboard | `/manager/dashboard/` | `templates/manager_dashboard/dashboard.html` | `managers.views.manager_dashboard` | `start_date` | `end_date` | `period=custom` | `23:59:59.999999` (Inclusive) | Branch filter. Telecaller call volume, connection rates, conversion metrics. |
| **9** | Telecaller Dashboard | `/telecaller/dashboard/` | `templates/telecaller_dashboard/dashboard.html` | `telecallers.views.telecaller_dashboard` | `start_date` | `end_date` | `period=custom` | `23:59:59.999999` (Inclusive) | Telecaller-scoped KPIs: calls dialed, talk time, connected leads, callbacks. |
| **10** | Admin Calls Listing | `/admin/calls/` | `templates/admin/calls_list.html` | `calls.views.admin_calls_list` | `date_from` | `date_to` | None | `time.max` (Inclusive) | Search `search`, status, outcome, manager, telecaller, branch. Paginated. |
| **11** | Call Recordings Listing | `/call-recordings/recordings/` | `templates/calls/recordings_list.html` | `drive.views.call_recordings_list` | `date_from` | `date_to` | None | `time.max` (Inclusive) | Search `q`, telecaller, match, direction. Paginated. |
| **12** | Admin Follow-ups Listing | `/admin/followups/` | `templates/admin/followups_list.html` | `followups.views.admin_followups_list` | `date_from` | `date_to` | None | Inclusive Date comparison | Search `search`, status, manager, telecaller, branch, product, channel. Paginated. |
| **13** | Counselor Follow-ups Listing | `/counselor/followups/` | `templates/counselor/followups_list.html` | `followups.views.counselor_followups_list` | `date_from` | `date_to` | None | Inclusive Date comparison | Search `search`, status, telecaller, branch, product, channel. Paginated. |
| **14** | Admin Reports | `/admin/reports/` | `templates/reports/admin_reports.html` | `reports.views.admin_reports` | `date_from` | `date_to` | None | `23:59:59.999999` (Inclusive) | Branch, counselor, telecaller. Conversion funnels and lead flow. |
| **15** | Manager Reports (Dashboard Report) | `/manager/reports/` | `templates/reports/dashboard_report.html` | `reports.views.manager_reports` | `start_date` | `end_date` | `date_filter=custom` | `time.max` (Inclusive) | Branch, channel. Channel distribution, branch matrix, trends. |
| **16** | Telecaller RnR Report | `/reports/telecaller-rnr/` | `templates/reports/telecaller_rnr_report.html` | `reports.views.telecaller_rnr_report` | `start_date` | `end_date` | `period=custom` | `time.max` (Inclusive) | Branch, counselor, search. CSV Export (`?export=csv`) uses active date filter. |
| **17** | Finance Dashboard | `/finance/dashboard/` | `templates/finance/dashboard.html` | `finance.views.finance_dashboard` | `start_date` | `end_date` | `period=custom` | `23:59:59.999999` (Inclusive) | Branch, product. Revenue collections, dues, installment projections. |
| **18** | Receptionist Walk-in Dashboard | `/receptionist/dashboard/` | `templates/receptionist/dashboard.html` | `leads.views.receptionist_dashboard` | `from_date` | `to_date` | None | `time.max` (Inclusive) | Search `search`, branch, lead type, status, assignment. Paginated. |

---

## 3. Safe Wiring Plan (CTO Specification)

### A. Core Component Integration
1. **Asset Deployment**:
   - `static/js/date-range-picker.js` (vanilla JS, zero dependencies, auto-initialization via `DrpInit()`).
   - `static/css/date-range-picker.css` (mapped to CRM design system tokens: `--tp-surface-card`, `--tp-text-primary`, `--tp-surface-border`, `--tp-surface-card-hover`, `--tp-primary-600`).
2. **Base Template**:
   - Loaded **ONCE** in `templates/base.html`:
     ```html
     <link rel="stylesheet" href="{% static 'css/date-range-picker.css' %}?v=20261030_compact">
     <script src="{% static 'js/date-range-picker.js' %}?v=20261030_compact" defer></script>
     ```
3. **Shared Django Partial (`templates/partials/date_range_picker.html`)**:
   ```html
   <div class="drp-root {{ extra_class|default:'' }}"
        data-from-name="{{ from_name|default:'date_from' }}"
        data-to-name="{{ to_name|default:'date_to' }}"
        data-autosubmit="{{ autosubmit|default:'true' }}"
        {% if label %}data-label="{{ label }}"{% endif %}
        {% if min_date %}data-min-date="{{ min_date }}"{% endif %}
        {% if max_date %}data-max-date="{{ max_date }}"{% endif %}>
     <input type="hidden" name="{{ from_name|default:'date_from' }}" value="{{ from_val|default:'' }}">
     <input type="hidden" name="{{ to_name|default:'date_to' }}" value="{{ to_val|default:'' }}">
     {% if period_name %}
     <input type="hidden" name="{{ period_name }}" value="{{ period_val|default:'custom' }}" data-drp-period="1">
     {% endif %}
   </div>
   ```

### B. Form-Level Wiring Per Category
1. **Standard Listing Pages** (`/admin/leads/`, `/admin/leads/new/`, `/admin/calls/`, `/call-recordings/recordings/`, `/admin/followups/`, `/counselor/followups/`, `/admin/reports/`):
   - Replace old trigger/inputs with:
     ```html
     {% include "partials/date_range_picker.html" with from_name="date_from" to_name="date_to" from_val=date_from to_val=date_to %}
     ```
2. **Dashboards with Canonical `start_date` / `end_date`** (`/accountant/dashboard/`, `/accountant/verification/`, `/branch-head/dashboard/`, `/counselor/dashboard/`, `/manager/dashboard/`, `/telecaller/dashboard/`, `/finance/dashboard/`):
   - Replace old trigger/inputs with:
     ```html
     {% include "partials/date_range_picker.html" with from_name="start_date" to_name="end_date" from_val=start_date to_val=end_date period_name="period" period_val="custom" %}
     ```
3. **Dashboards with `from_date` / `to_date`** (`/admin/dashboard/`, `/receptionist/dashboard/`):
   - Replace old trigger/inputs with:
     ```html
     {% include "partials/date_range_picker.html" with from_name="from_date" to_name="to_date" from_val=from_date to_val=to_date %}
     ```
4. **Reports Requiring Explicit Preset Overrides** (`/manager/reports/`, `/reports/telecaller-rnr/`):
   - For `reports/dashboard_report.html`: `from_name="start_date"` `to_name="end_date"` `period_name="date_filter"` `period_val="custom"`.
   - For `reports/telecaller_rnr_report.html`: `from_name="start_date"` `to_name="end_date"` `period_name="period"` `period_val="custom"`.

### C. Safety Guarantees
- **No Backend Changes**: Zero modifications to view query filtering, timezone logic (`Asia/Kolkata`), or database date boundaries (`time.min` to `time.max`).
- **Filter Preservation**: Form submission retains existing query parameters (search, branch, telecaller, status, stage).
- **Pagination Reset**: Submitting any new date range automatically resets to `page=1`.
- **Theme Adaptivity**: Fully responsive CSS tokens for both Light (`:root`, `data-theme="light"`) and Dark (`[data-theme="dark"]`, `html[data-theme="dark"]`) themes.
- **Decommissioning Guard**: Old drawer / smart popover JavaScript and CSS will only be removed after all 18 pages have been verified and signed off.

---

## 4. Verification & QA Protocol (Step 4 & 5)
1. **Automated Click & Auto-Submit Verification**: Verify 1st click = From, 2nd click = To, auto-submits.
2. **Record Count Equality Verification**: Execute before vs. after query tests across all 18 pages to verify that record counts match 100%.
3. **Interaction Edge Cases**:
   - Reverse selection (To clicked before From).
   - Escape key cancels in-progress range without submitting.
   - Clear link resets date filter to empty.
   - Keyboard navigation (arrows, Enter, Space).
4. **Responsive Layouts**: Verified at 360, 390, 768, 1366, and 1920 px.
5. **Theme Verification**: Verified in Light and Dark modes.
