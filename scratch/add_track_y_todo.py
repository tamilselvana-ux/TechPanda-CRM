path = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\TODO.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

track_y = '''

---

## Track Y: 48-Hour Rolling Auto-Sync & Manual Historical Override Engine

- [ ] **Item 167 — CallSync & Recording 48-Hour Rolling Auto-Sync Horizon**:
  - What: Set default background auto-sync horizon to 48 hours for both phone call logs (`CALL_SYNC_MAX_AGE_HOURS = 48`) and call audio recordings (`RECORDING_MAX_AGE_HOURS = 48`) in `calls/conf.py` and `calls/sync_services.py`. In normal automatic sync, any incoming log/audio older than 48 hours is skipped as stale, since previously synced data is already safely stored in the CRM database.
  - Where: `CRM/calls/conf.py`, `CRM/calls/sync_services.py`.
  - Acceptance checks: Default rolling auto-sync ignores phone logs and recordings older than 48 hours; fresh calls (within 48 hours) sync seamlessly.
  - Status: ⬜.

- [ ] **Item 168 — Manual Historical Sync Override & Device Custom Range**:
  - What: Add `manual_override` / `sync_all` parameter support to `calls/sync_services.py` (`ingest_calls`, `save_recording`) and `calls/api_views.py` (`CallIngestView`, `RecordingUploadView`). Add `allow_historical_sync` boolean to `CallDevice` model so an administrator can manually enable full historical sync or specify an exact historical cutoff date (`sync_cutoff_date`) per device.
  - Where: `CRM/calls/sync_services.py`, `CRM/calls/api_views.py`, `CRM/calls/models.py`.
  - Acceptance checks: When `manual_override=True` or `allow_historical_sync=True`, calls/recordings older than 48 hours are accepted up to the custom cutoff or all time; auto-sync remains safely constrained to 48 hours.
  - Status: ⬜.

- [ ] **Item 169 — Admin Call Device Management & Device Sync Controls**:
  - What: Expose `sync_cutoff_date` and `allow_historical_sync` in `CallDeviceAdmin` (`calls/admin.py`), and add an administrative API endpoint (`/calls/device/<id>/update-sync-settings/`) allowing admins to toggle manual override and set custom sync horizons.
  - Where: `CRM/calls/admin.py`, `CRM/calls/views.py`, `CRM/calls/urls.py`.
  - Acceptance checks: Admins can view connected devices, toggle historical sync override, and set custom sync dates.
  - Status: ⬜.

- [ ] **Item 170 — Comprehensive Automated Verification Suite**:
  - What: Automated regression test verifying: 1) Normal auto-sync enforces 48-hour cutoff (calls older than 48h skipped); 2) Manual override bypasses 48h restriction and allows historical call sync; 3) Recording upload enforces 48h cutoff on auto-sync and accepts older audio with manual override; 4) Facebook Leads 48-hour auto-sync and manual modal presets remain active; 5) `manage.py check` passes with 0 issues; 6) `stub_scan.py` passes with 0 blockers.
  - Where: `CRM/scratch/test_48h_sync_and_override.py`.
  - Acceptance checks: 100% test pass rate, 0 Django check errors, 0 stub scan blockers.
  - Status: ⬜.
'''

content += track_y

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully added Track Y to TODO.md")
