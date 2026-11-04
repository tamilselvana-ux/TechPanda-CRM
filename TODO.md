# DigiPanda CRM — Implementation Backlog (TODO.md)

## Track A: Shared Responsive Calendar Drawer (COMPLETED & SIGNED OFF)

- [x] **Item 01 · Shared Drawer Base Component**: Create `templates/components/calendar_drawer.html`, `static/css/calendar-drawer.css`, and `static/js/calendar-drawer.js`. Include once in `templates/base.html`.
- [x] **Item 02 · Admin Dashboard Date Drawer**: Integrate calendar drawer trigger on `/admin/dashboard/` (`templates/admin_dashboard/dashboard.html`).
- [x] **Item 03 · Accountant Dashboard Date Drawer**: Integrate calendar drawer trigger on `/accountant/dashboard/` (`templates/accountant/dashboard.html`).
- [x] **Item 04 · Accountant Verification Queue Date Drawer**: Integrate calendar drawer trigger on `/accountant/verification/` (`templates/accountant/verification_list.html`).
- [x] **Item 05 · Admin Leads Listing Date Drawer**: Integrate calendar drawer trigger on `/admin/leads/` (`templates/admin/leads_list.html`).
- [x] **Item 06 · Admin New Leads Queue Date Drawer**: Integrate calendar drawer trigger on `/admin/leads/new/` (`templates/admin/new_leads_list.html`).
- [x] **Item 07 · Branch Head Dashboard Date Drawer**: Integrate calendar drawer trigger on `/branch-head/dashboard/` (`templates/branch_head_dashboard/dashboard.html`).
- [x] **Item 08 · Counselor Dashboard Date Drawer**: Integrate calendar drawer trigger on `/counselor/dashboard/` (`templates/counselor_dashboard/dashboard.html`).
- [x] **Item 09 · Sales Head Dashboard Date Drawer**: Integrate calendar drawer trigger on `/manager/dashboard/` (`templates/manager_dashboard/dashboard.html`).
- [x] **Item 10 · Telecaller Dashboard Date Drawer**: Integrate calendar drawer trigger on `/telecaller/dashboard/` (`templates/telecaller_dashboard/dashboard.html`).
- [x] **Item 11 · Admin Calls Listing Date Drawer**: Integrate calendar drawer trigger on `/admin/calls/` (`templates/admin/calls_list.html`).
- [x] **Item 12 · Call Recordings Listing Date Drawer**: Integrate calendar drawer trigger on `/calls/recordings/` (`templates/calls/recordings_list.html`).
- [x] **Item 13 · Admin Follow-ups Listing Date Drawer**: Integrate calendar drawer trigger on `/admin/followups/` (`templates/admin/followups_list.html`).
- [x] **Item 14 · Counselor Follow-ups Listing Date Drawer**: Integrate calendar drawer trigger on `/counselor/followups/` (`templates/counselor/followups_list.html`).
- [x] **Item 15 · Analytics & Performance Reports Date Drawer**: Integrate calendar drawer trigger on `/reports/` (`templates/reports/admin_reports.html`).
- [x] **Item 16 · Marketing & Performance Report Date Drawer**: Integrate calendar drawer trigger on `/reports/dashboard-report/` (`templates/reports/dashboard_report.html`).
- [x] **Item 17 · Telecaller RNR Report Date Drawer**: Integrate calendar drawer trigger on `/reports/telecaller-rnr/` (`templates/reports/telecaller_rnr_report.html`).
- [x] **Item 18 · Finance Dashboard & Oversight Date Drawer**: Integrate calendar drawer trigger on `/finance/dashboard/` (`templates/finance/dashboard.html`).
- [x] **Item 19 · Final Device & Role Verification**: Run automated verification across all 17 pages at 360, 390, 768, 1024, 1366, 1920 px in Light and Dark themes.

---

## Track B: Filter-Aware Clickable KPI Cards (COMPLETED & SIGNED OFF)

- [x] **Item 20 · KPI Master Mapping & Single Source of Truth**: Create validated KPI registry and shared filtering function (`leads/kpi_registry.py`).
- [x] **Item 21 · Admin Dashboard Clickable KPIs**: Convert all 8 KPI cards to filter-preserving drill-down links.
- [x] **Item 22 · Branch Head Dashboard Clickable KPIs**: Convert branch KPI tiles to filter-preserving links and wire `branch_head_leads_list`.
- [x] **Item 23 · Sales Head Dashboard Clickable KPIs**: Convert manager KPI tiles to filter-preserving links and wire `manager_leads_list`, `manager_calls_list`, and `manager_followups_list`.
- [x] **Item 24 · Counselor Dashboard Clickable KPIs**: Convert counselor KPI tiles to filter-preserving links and wire `counselor_leads_list`.
- [x] **Item 25 · Telecaller Dashboard Clickable KPIs**: Convert telecaller KPI tiles to filter-preserving links.
- [x] **Item 26 · Target Listing Active Filter Bar & KPI Chips**: Add active filters chip banner with "Clear Filter" option across all listing pages.
- [x] **Item 27 · KPI Automated Equality Verification**: Run automated tests verifying KPI count == drill-down table total == database count (100% verified).


---

## Track C: Compact Date Range Picker Rollout (18 Pages)

- [x] **Item 28 — Shared Assets & Include Partial**: Load `static/js/date-range-picker.js` and `static/css/date-range-picker.css` in `templates/base.html`. Implement `templates/partials/date_range_picker.html`.
- [x] **Item 29 — Admin Dashboard**: Integrate compact picker on `/admin/dashboard/` (`templates/admin_dashboard/dashboard.html` with `from_date` / `to_date`).
- [x] **Item 30 — Accountant Dashboard**: Integrate compact picker on `/accountant/dashboard/` (`templates/accountant/dashboard.html` with `start_date` / `end_date`).
- [x] **Item 31 — Accountant Verification Queue**: Integrate compact picker on `/accountant/verification/` (`templates/accountant/verification_list.html` with `start_date` / `end_date`).
- [x] **Item 32 — Admin Leads Listing**: Integrate compact picker on `/admin/leads/` (`templates/admin/leads_list.html` with `date_from` / `date_to`).
- [x] **Item 33 — Admin New Leads Queue**: Integrate compact picker on `/admin/leads/new/` (`templates/admin/new_leads_list.html` with `date_from` / `date_to`).
- [x] **Item 34 — Branch Head Dashboard**: Integrate compact picker on `/manager/branch-head/dashboard/` (`templates/branch_head_dashboard/dashboard.html` with `start_date` / `end_date`).
- [x] **Item 35 — Counselor Dashboard**: Integrate compact picker on `/counselor/dashboard/` (`templates/counselor_dashboard/dashboard.html` with `start_date` / `end_date`).
- [x] **Item 36 — Sales Head / Manager Dashboard**: Integrate compact picker on `/manager/dashboard/` (`templates/manager_dashboard/dashboard.html` with `start_date` / `end_date`).
- [x] **Item 37 — Telecaller Dashboard**: Integrate compact picker on `/telecaller/dashboard/` (`templates/telecaller_dashboard/dashboard.html` with `start_date` / `end_date`).
- [x] **Item 38 — Admin Calls Listing**: Integrate compact picker on `/admin/calls/` (`templates/admin/calls_list.html` with `date_from` / `date_to`).
- [x] **Item 39 — Call Recordings Listing**: Integrate compact picker on `/call-recordings/recordings/` (`templates/calls/recordings_list.html` with `date_from` / `date_to`).
- [x] **Item 40 — Admin Follow-ups Listing**: Integrate compact picker on `/admin/followups/` (`templates/admin/followups_list.html` with `date_from` / `date_to`).
- [x] **Item 41 — Counselor Follow-ups Listing**: Integrate compact picker on `/counselor/followups/` (`templates/counselor/followups_list.html` with `date_from` / `date_to`).
- [x] **Item 42 — Admin Reports**: Integrate compact picker on `/admin/reports/` (`templates/reports/admin_reports.html` with `date_from` / `date_to`).
- [x] **Item 43 — Manager Reports (Dashboard Report)**: Integrate compact picker on `/manager/reports/` (`templates/reports/dashboard_report.html` with `start_date` / `end_date` and `date_filter=custom`).
- [x] **Item 44 — Telecaller RnR Report**: Integrate compact picker on `/reports/telecaller-rnr/` (`templates/reports/telecaller_rnr_report.html` with `start_date` / `end_date` and `period=custom`).
- [x] **Item 45 — Finance Dashboard**: Integrate compact picker on `/finance/dashboard/` (`templates/finance/dashboard.html` with `start_date` / `end_date`).
- [x] **Item 46 — Receptionist Walk-in Dashboard**: Integrate compact picker on `/receptionist/dashboard/` (`templates/receptionist/dashboard.html` with `from_date` / `to_date`).
- [x] **Item 47 — Decommissioning & Full Automated QA**: Remove obsolete drawer CSS/JS/HTML artifacts once all 18 pages are verified with identical record counts, keyboard navigation, responsive layout checks (360, 390, 768, 1366, 1920 px), and Light & Dark theme screenshots.

---

## Track D: UI Polish, Calendar Popover Fix & Exact Receipt Email Template

- [x] **Item 48 — Date Range Calendar Popover Cutoff & Stacking Context**: Remove card overflow clipping (`.tp-card:has(.drp-root)`, `.tp-filter-bar`, `.filter-card { overflow: visible !important; }`), set popover `z-index: 9999 !important;`, ensuring the full calendar grid (all 6 weeks) and footer actions ("Select start date" / "Clear") render cleanly without clipping.
- [x] **Item 49 — Admin Dashboard Filter Row UI Bugs (Chevrons & Layout)**: Fix double chevrons on select inputs in `crm.css` and `design-system.css` (`appearance: none !important; -webkit-appearance: none !important; -moz-appearance: none !important;`), add `padding-right: 32px !important;`, adjust `.tp-filter-field` sizing (`flex: 1 1 140px; min-width: 140px;`), and refine action button spacing.
- [x] **Item 50 — Authorized Signature Image Integration**: Embed newly uploaded signature (`media_1793315857664_1a539462.png`, `Shashikala.k`) cleanly into `static/images/shashi_sign.png` and `static/images/authorized_signature.png`, preserving proportional 4:1 aspect ratio above the signatory rule across web receipt, PDF receipt, and email.
- [x] **Item 51 — Payment Receipt Email Template Exact Match**: Re-align `templates/emails/payment_receipt.html`, `templates/leads/receipt.html`, and `templates/leads/receipt_pdf.html` to match reference PDF `DigiPanda_Tax_Invoice_TP12519.pdf` and mobile email preview. Update `leads/constants.py` with canonical GSTIN `33AAMCT5031F1ZJ`, PAN `AAMCT5031F`, phone `9884678282`, email `admin@digipanda.com`, website `www.digipanda.com`. Ensure all remaining "TechPanda" references are replaced with "DigiPanda".
- [x] **Item 52 — Full Verification & Automated Regression Suite**: Run Django system check, verify email rendering, test PDF generation, and verify filter bar and calendar popup across desktop and mobile.

---

## Track E: Modern 3D Cinematic Redesign, Business Dashboards, Meta Plan & Professional Emails

- [x] **Item 53 — Modern 3D Cinematic Visual Language & Global Experience**:
  - Create `static/css/modern-3d-cinematic.css` and `static/js/modern-3d-cinematic.js` (loaded in `base.html`).
  - Specular glassmorphism (`backdrop-filter: blur(14px)`), ambient holographic mesh, dynamic 3D card tilt & perspective on hover, glowing badge chips, micro-lighting rims, and 60 FPS `prefers-reduced-motion` compliance across both Obsidian Dark and Radiant Titanium Light modes.
- [x] **Item 54 — Enterprise Business Standards Redesign for All Dashboards**:
  - **Item 54a**: Admin Dashboard (`/admin/dashboard/`, `templates/admin_dashboard/dashboard.html`)
  - **Item 54b**: Accountant & Finance Dashboards (`/accountant/dashboard/`, `/finance/dashboard/`)
  - **Item 54c**: Branch Head Dashboard (`/manager/branch-head/dashboard/`)
  - **Item 54d**: Sales Head / Manager Dashboard (`/manager/dashboard/`)
  - **Item 54e**: Counselor Dashboard (`/counselor/dashboard/`)
  - **Item 54f**: Telecaller Dashboard (`/telecaller/dashboard/`)
  - **Item 54g**: Receptionist Walk-in Dashboard (`/receptionist/dashboard/`)
- [x] **Item 55 — Meta Leads Separation Plan: Facebook vs Instagram (Plan-Only)**:
  - Deliver `docs/plan_meta_leads_facebook_vs_instagram.md` detailing Meta Webhook & Graph API `platform` parsing, database schema enhancements, Google Sheet ingestion adjustments, UI filter updates, and historical data migration strategy.
- [x] **Item 56 — Professional Student Enrollment & Installment Reminder Email Templates**:
  - Re-align `templates/emails/enrollment_confirmation.html` (Student Enrollment Welcome) and `templates/emails/installment_reminder.html` (Fee Payment Reminder) with executive typography, mobile-responsive layout, portal onboarding, bank/UPI details, and zero broken markup.
- [x] **Item 57 — Automated Verification & QA Sign-Off**:
  - Run Django system check, test email rendering, verify 3D cinematic scripts and dashboard responsiveness at 360, 390, 768, 1024, 1366, 1920 px.

---

## Track F: Meta Leads Separation Execution & Executive Dashboard Polish

- [x] **Item 58 — Date Range & Filter Bar Layout Polish (Fix Overlapping Button)**:
  - Eliminate overlap between Date Range button and adjacent dropdowns by establishing a 2-tier executive toolbar (Tier 1: Quick period presets + Date Range picker + Reset; Tier 2: Entity filter dropdowns + Filter/Reset actions with `min-width: 150px; flex: 1 1 160px;`).
- [ ] **Item 59 — High-Standard Executive Dashboard Visual Overhaul**:
  - Re-architect Section 1 ("Operational Velocity & Workload") from an awkward 6 + 1 card wrap into balanced executive tiers: Primary Pipeline Pulse (4 cards in 4-col grid) and Telecalling Engagement (3 cards in 3-col grid).
  - Standardize Section 2 ("Admissions, Revenue & Fee Collections") into a crisp 5-col grid with executive top accents, tabular numerals, and status indicators.
- [ ] **Item 60 — Execute Meta Leads Separation Plan (Facebook vs Instagram)**:
  - Add `Instagram` to `CANONICAL_LEAD_SOURCES` and update `normalize_lead_source()` in `leads/models.py`.
  - Add `platform` field to `Lead` model and run migrations.
  - Ensure `Instagram Ads` channel is seeded in `channels.Channel`.
  - Update ingestion and spreadsheet sync to parse `"ig"` / `"instagram"` vs `"fb"` / `"facebook"`.
  - Expose separate Facebook and Instagram choices in dashboard and listing filters.
- [ ] **Item 61 — Full QA Verification & Automated Test Suite**:
  - Run `python manage.py check`, `python manage.py makemigrations --check`, and automated visual and regression test suites.
