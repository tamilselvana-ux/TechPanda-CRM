fpath = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\TODO.md"
with open(fpath, "r", encoding="utf-8") as f:
    text = f.read()

target = """## Track W: Facebook Lead Ads Date Filter & Auto-Sync Cutoff Shield

- [ ] **Item 157 — Backend Core Date-Filtered Lead Sync (`fb_leads/facebook.py`)**:
  - What: Add `since` and `until` date filtering (Unix timestamps and datetime) to `sync_page_leads` and `sync_all_leads`. Query Meta Graph API `/{form_id}/leads` with `since` and `until` parameters, validate `created_time` per lead, and halt pagination immediately when older records appear.
  - Where: `CRM/fb_leads/facebook.py`.
  - Acceptance checks: `sync_page_leads` accepts `since` and `until` timestamps/datetimes; Graph API parameters include `since`/`until`; pagination halts early on older leads.
  - Status: ⬜.

- [ ] **Item 158 — Page Cutoff Date Model & Migration (`fb_leads/models.py`)**:
  - What: Add `sync_cutoff_date` (`DateField(null=True, blank=True)`) to `FacebookPage` so administrators can set a permanent historical boundary (e.g. "Only leads from 2026-11-01 onwards"), preventing old/deleted leads from ever re-importing.
  - Where: `CRM/fb_leads/models.py`, `CRM/fb_leads/migrations/`.
  - Acceptance checks: Schema has `sync_cutoff_date`; migration applies cleanly; `FacebookPage` instances can store and query cutoff date.
  - Status: ⬜.

- [ ] **Item 159 — Smart Rolling Horizon Auto-Sync Engine (`fb_leads/scheduler.py`)**:
  - What: Update `run_auto_sync_cycle()` so background automatic sync checks only a rolling 48-hour window (or since `last_sync_at - 1 hour`), respecting any configured `sync_cutoff_date`, preventing full 1-year historical re-downloads even if the local database is cleared.
  - Where: `CRM/fb_leads/scheduler.py`.
  - Acceptance checks: Auto-sync passes `since` boundary; respects `page.sync_cutoff_date`; prevents scanning all of history every 3 minutes.
  - Status: ⬜.

- [ ] **Item 160 — Controller & Views Date Parameter Support (`fb_leads/views.py`)**:
  - What: Update `sync_leads` (global sync) and `fb_page_sync` (per-page sync) to parse `sync_mode` (`today`, `yesterday`, `7days`, `custom`, `all`), `start_date`, and `end_date`, and add view endpoint for updating a page's `sync_cutoff_date`.
  - Where: `CRM/fb_leads/views.py`, `CRM/fb_leads/urls.py`.
  - Acceptance checks: Endpoints parse dates into timestamps; pass them to sync engine; return sync count feedback; allow saving cutoff date via AJAX.
  - Status: ⬜.

- [ ] **Item 161 — Interactive Date Picker Sync Modal UI (`fb_leads/templates/fb_leads/leads.html` & `accounts.html`)**:
  - What: Replace blind "Sync All Leads" button with an interactive "Sync Leads" modal offering "Today Only", "Yesterday & Today", "Last 7 Days", "Custom Range" (with date pickers), and "All Time". Add inline "Sync From Date" field on each connected Facebook Page in `accounts.html`.
  - Where: `CRM/fb_leads/templates/fb_leads/leads.html`, `CRM/fb_leads/templates/fb_leads/accounts.html`.
  - Acceptance checks: Modal opens on click; allows selecting presets or custom date range; displays loading spinner during sync; displays cutoff date input in page settings with instant save.
  - Status: ⬜.

- [ ] **Item 162 — Comprehensive Automated Verification Suite**:
  - What: Automated regression test verifying: 1) `since` timestamp correctly restricts leads from Facebook API; 2) older leads outside the date range are skipped; 3) background scheduler applies the cutoff date; 4) UI views accept date parameters without errors; 5) `manage.py check` passes with 0 issues; 6) `stub_scan.py` passes with 0 blockers.
  - Where: `CRM/scratch/test_fb_date_sync.py`.
  - Acceptance checks: 100% test pass rate, 0 Django check errors, 0 stub scan blockers.
  - Status: ⬜."""

replacement = """## Track W: Facebook Lead Ads Date Filter & Auto-Sync Cutoff Shield

- [x] **Item 157 — Backend Core Date-Filtered Lead Sync (`fb_leads/facebook.py`)**:
  - What: Add `since` and `until` date filtering (Unix timestamps and datetime) to `sync_page_leads` and `sync_all_leads`. Query Meta Graph API `/{form_id}/leads` with `since` and `until` parameters, validate `created_time` per lead, and halt pagination immediately when older records appear.
  - Where: `CRM/fb_leads/facebook.py`.
  - Proof: Implemented `_to_timestamp` helper supporting `datetime`, `date`, Unix timestamp, and string `YYYY-MM-DD` inputs. Updated `sync_page_leads(page_id, since=None, until=None)` to calculate effective timestamps, forward `since` and `until` to Meta Graph API, validate `created_time` per lead, and early-halt pagination on older submissions. Updated `sync_all_leads(since=None, until=None)`.
  - Status: ✅.

- [x] **Item 158 — Page Cutoff Date Model & Migration (`fb_leads/models.py`)**:
  - What: Add `sync_cutoff_date` (`DateField(null=True, blank=True)`) to `FacebookPage` so administrators can set a permanent historical boundary (e.g. "Only leads from 2026-11-01 onwards"), preventing old/deleted leads from ever re-importing.
  - Where: `CRM/fb_leads/models.py`, `CRM/fb_leads/migrations/0006_facebookpage_sync_cutoff_date.py`, `CRM/fb_leads/apps.py`.
  - Proof: Added `sync_cutoff_date` to `FacebookPage` model. Generated and applied migration `0006_facebookpage_sync_cutoff_date.py`. Added MySQL self-healing schema check in `fb_leads/apps.py` to prevent production column drift.
  - Status: ✅.

- [x] **Item 159 — Smart Rolling Horizon Auto-Sync Engine (`fb_leads/scheduler.py`)**:
  - What: Update `run_auto_sync_cycle()` so background automatic sync checks only a rolling 48-hour window (or since `last_sync_at - 1 hour`), respecting any configured `sync_cutoff_date`, preventing full 1-year historical re-downloads even if the local database is cleared.
  - Where: `CRM/fb_leads/scheduler.py`.
  - Proof: Updated `run_auto_sync_cycle()` in `fb_leads/scheduler.py` to calculate `auto_since = now - timedelta(hours=48)`, respecting `page.sync_cutoff_date` if configured. Updated `trigger_immediate_page_sync(page_id, since=None, until=None)` to accept and forward time filters.
  - Status: ✅.

- [x] **Item 160 — Controller & Views Date Parameter Support (`fb_leads/views.py`)**:
  - What: Update `sync_leads` (global sync) and `fb_page_sync` (per-page sync) to parse `sync_mode` (`today`, `yesterday`, `7days`, `custom`, `all`), `start_date`, and `end_date`, and add view endpoint for updating a page's `sync_cutoff_date`.
  - Where: `CRM/fb_leads/views.py`, `CRM/fb_leads/urls.py`.
  - Proof: Implemented `_parse_sync_time_range(request)` extracting presets or custom `start_date`/`end_date`. Updated `sync_leads` and `fb_page_sync` to forward date filters and log activity. Implemented `fb_page_update_cutoff` with JSON and form support and wired route in `fb_leads/urls.py`.
  - Status: ✅.

- [x] **Item 161 — Interactive Date Picker Sync Modal UI (`fb_leads/templates/fb_leads/leads.html` & `accounts.html`)**:
  - What: Replace blind "Sync All Leads" button with an interactive "Sync Leads" modal offering "Today Only", "Yesterday & Today", "Last 7 Days", "Custom Range" (with date pickers), and "All Time". Add inline "Sync From Date" field on each connected Facebook Page in `accounts.html`.
  - Where: `CRM/fb_leads/templates/fb_leads/leads.html`, `CRM/fb_leads/templates/fb_leads/accounts.html`.
  - Proof: Replaced single sync button with an interactive modal in `leads.html` featuring time-range radio presets, custom start/end date inputs, and sync loading state. Added "Sync Cutoff Date" column in `accounts.html` with inline date picker and live AJAX auto-save (`updatePageCutoff`).
  - Status: ✅.

- [x] **Item 162 — Comprehensive Automated Verification Suite**:
  - What: Automated regression test verifying: 1) `since` timestamp correctly restricts leads from Facebook API; 2) older leads outside the date range are skipped; 3) background scheduler applies the cutoff date; 4) UI views accept date parameters without errors; 5) `manage.py check` passes with 0 issues; 6) `stub_scan.py` passes with 0 blockers.
  - Where: `CRM/scratch/test_fb_date_sync.py`.
  - Proof: Executed `scratch/test_fb_date_sync.py` verifying all 4 suites: `_to_timestamp` conversions, `sync_page_leads` with `since=today` and cutoff date filtering (1-year old lead blocked), view time range parsing, and HTTP 200 UI rendering. `manage.py check` passed with 0 issues, and `stub_scan.py` passed with 0 blockers.
  - Status: ✅."""

text = text.replace('\r\n', '\n')
target = target.replace('\r\n', '\n')
replacement = replacement.replace('\r\n', '\n')

if target in text:
    text = text.replace(target, replacement, 1)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated TODO.md with completed Track W")
else:
    print("Target not found in TODO.md")
