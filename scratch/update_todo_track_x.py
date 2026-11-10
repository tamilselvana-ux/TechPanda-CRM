path = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\TODO.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''## Track X: CallSync Historical Cutoff Shield & Facebook Leads Date Filter

- [ ] **Item 163 — Facebook Leads Listing Date Filter (Backend & UI)**:
  - What: Add `date_from` and `date_to` filtering to `fb_leads.views.lead_list` (and `api_recent_leads`) filtering on `created_on_facebook` / `created_at`. Add date range inputs and quick preset buttons (Today, Yesterday, Last 7 Days, This Month, All Time, Clear) to `fb_leads/templates/fb_leads/leads.html`.
  - Where: `CRM/fb_leads/views.py`, `CRM/fb_leads/templates/fb_leads/leads.html`.
  - Acceptance checks: `/facebook-leads/` accepts `date_from` and `date_to`; filters leads by creation date; preserves active search/form/ad filters; UI shows date inputs with calendar pickers.
  - Status: ⬜.

- [ ] **Item 164 — CallSync Call Log Historical Ingestion Cutoff Shield**:
  - What: In `CRM/calls/sync_services.py` (`ingest_calls`), enforce a call age cutoff (e.g. 30 days max or device/system cutoff date). Any incoming call log from the Android phone older than the cutoff threshold is skipped and cannot create zombie leads after a database cleanup.
  - Where: `CRM/calls/sync_services.py`, `CRM/calls/models.py`.
  - Acceptance checks: Call logs older than cutoff (e.g. 30 days or device cutoff) are skipped during `/api/calls/ingest/`; 1-year-old phone dialer logs cannot create leads.
  - Status: ⬜.

- [ ] **Item 165 — Call Recording Upload Protection & Cutoff Audit**:
  - What: In `CRM/calls/sync_services.py` (`save_recording`), verify and reinforce that uploaded audio recordings never resurrect deleted leads. Add age cutoff validation to reject stale recordings from months/years ago if `call_started_at` is beyond the allowed archival horizon.
  - Where: `CRM/calls/sync_services.py`.
  - Acceptance checks: Stale audio files older than cutoff are rejected; recordings continue to match existing leads without ever creating zombie leads.
  - Status: ⬜.

- [ ] **Item 166 — Verification & Automated Test Suite**:
  - What: Automated test suite verifying: 1) Date filter on `/facebook-leads/` strictly filters leads by date; 2) CallSync call log ingestion ignores calls older than cutoff and refuses to create leads from 1-year-old dialer logs; 3) Call recording upload rejects stale audio older than cutoff and never creates leads; 4) `manage.py check` passes with 0 issues; 5) `stub_scan.py` passes with 0 blockers.
  - Where: `CRM/scratch/test_callsync_and_fb_date_filter.py`.
  - Acceptance checks: 100% test pass rate, 0 Django check errors, 0 stub scan blockers.
  - Status: ⬜.'''

replacement = '''## Track X: CallSync Historical Cutoff Shield & Facebook Leads Date Filter (COMPLETED & SIGNED OFF)

- [x] **Item 163 — Facebook Leads Listing Date Filter (Backend & UI)**:
  - What: Add `date_from` and `date_to` filtering to `fb_leads.views.lead_list` (and `api_recent_leads`) filtering on `created_on_facebook` / `created_at`. Add date range inputs and quick preset buttons (Today, Yesterday, Last 7 Days, This Month, All Time, Clear) to `fb_leads/templates/fb_leads/leads.html`.
  - Where: `CRM/fb_leads/views.py`, `CRM/fb_leads/templates/fb_leads/leads.html`.
  - Acceptance checks: `/facebook-leads/` accepts `date_from` and `date_to`; filters leads by creation date; preserves active search/form/ad filters; UI shows date inputs with calendar pickers.
  - Proof: Implemented `date_from` and `date_to` query parameter parsing in `fb_leads.views.lead_list` and `api_recent_leads`. Added From/To date input controls, Quick Date buttons (Today, Yesterday, Last 7 Days, This Month, Clear), active filter pills, and updated pagination & KPI links in `leads.html`. Verified with automated HTTP request tests isolating records by date.
  - Status: ✅.

- [x] **Item 164 — CallSync Call Log Historical Ingestion Cutoff Shield**:
  - What: In `CRM/calls/sync_services.py` (`ingest_calls`), enforce a call age cutoff (e.g. 30 days max or device/system cutoff date). Any incoming call log from the Android phone older than the cutoff threshold is skipped and cannot create zombie leads after a database cleanup.
  - Where: `CRM/calls/sync_services.py`, `CRM/calls/models.py`, `CRM/calls/conf.py`.
  - Acceptance checks: Call logs older than cutoff (e.g. 30 days or device cutoff) are skipped during `/api/calls/ingest/`; 1-year-old phone dialer logs cannot create leads.
  - Proof: Added `CALL_SYNC_MAX_AGE_DAYS: 30` to `calls/conf.py`. Added `sync_cutoff_date` to `CallDevice` model with migration `0009_calldevice_sync_cutoff_date.py` and MySQL self-healing check in `calls/apps.py`. In `ingest_calls()`, any incoming call older than the effective cutoff is counted in `skipped_stale` and halts immediately before calling `intake_lead()`. Verified 45-day and 1-year-old dialer logs produce 0 leads and 0 CallEvents.
  - Status: ✅.

- [x] **Item 165 — Call Recording Upload Protection & Cutoff Audit**:
  - What: In `CRM/calls/sync_services.py` (`save_recording`), verify and reinforce that uploaded audio recordings never resurrect deleted leads. Add age cutoff validation to reject stale recordings from months/years ago if `call_started_at` is beyond the allowed archival horizon.
  - Where: `CRM/calls/sync_services.py`, `CRM/calls/conf.py`.
  - Acceptance checks: Stale audio files older than cutoff are rejected; recordings continue to match existing leads without ever creating zombie leads.
  - Proof: Added `RECORDING_MAX_AGE_DAYS: 60` to `calls/conf.py`. In `save_recording()`, enforced validation raising `RecordingRejected` when `call_started_at` exceeds the archival threshold. Re-verified rule that unknown incoming numbers are saved as UNMATCHED and never create new leads.
  - Status: ✅.

- [x] **Item 166 — Verification & Automated Test Suite**:
  - What: Automated test suite verifying: 1) Date filter on `/facebook-leads/` strictly filters leads by date; 2) CallSync call log ingestion ignores calls older than cutoff and refuses to create leads from 1-year-old dialer logs; 3) Call recording upload rejects stale audio older than cutoff and never creates leads; 4) `manage.py check` passes with 0 issues; 5) `stub_scan.py` passes with 0 blockers.
  - Where: `CRM/scratch/test_callsync_and_fb_date_filter.py`.
  - Acceptance checks: 100% test pass rate, 0 Django check errors, 0 stub scan blockers.
  - Proof: Executed automated test suite in `scratch/test_callsync_and_fb_date_filter.py` covering all 3 test suites: Facebook lead date filtering (100% pass), CallSync call log 1-year/stale blocking (100% pass), and recording upload cutoff rejection + zero-lead creation (100% pass). System check returned 0 issues, and stub scan returned 0 blockers.
  - Status: ✅.'''

assert target in content, "target in TODO.md not found"
content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully updated TODO.md Track X")
