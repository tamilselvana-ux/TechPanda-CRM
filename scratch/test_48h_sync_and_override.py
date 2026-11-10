import os, sys, django
sys.path.insert(0, r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import time
import json
from datetime import datetime, timedelta, timezone as dt_timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone

from accounts.models import User
from calls.models import CallDevice, CallEvent, CallEventType
from calls.sync_services import ingest_calls, save_recording, RecordingRejected
from drive.models import CallRecording
from leads.models import Lead

print("=" * 65)
print("RUNNING TRACK Y: 48-HOUR AUTO-SYNC & MANUAL OVERRIDE VERIFICATION")
print("=" * 65)

# Setup admin and telecaller
admin = User.objects.filter(is_superuser=True).first()
if not admin:
    admin = User.objects.filter(role='ADMIN').first()
assert admin is not None, "Admin user must exist"

telecaller = User.objects.filter(role='TELECALLER', is_active=True).first()
if not telecaller:
    telecaller = User.objects.create(
        username='test_tc_48h',
        email='test_tc_48h@test.com',
        role='TELECALLER',
        is_active=True
    )

device, _ = CallDevice.objects.get_or_create(user=telecaller)
device.sync_cutoff_date = None
device.allow_historical_sync = False
device.save()

# -------------------------------------------------------------------
# SUITE 1: 48-Hour Auto-Sync Horizon (Normal Background Sync)
# -------------------------------------------------------------------
print("\n[Suite 1] Testing 48-Hour Rolling Auto-Sync Horizon...")

phone_fresh_12h = '9666600001'
phone_stale_72h = '9666600002'

Lead.objects.filter(phone__in=[phone_fresh_12h, phone_stale_72h]).delete()
CallEvent.objects.filter(raw_number__in=[phone_fresh_12h, phone_stale_72h]).delete()

now = timezone.now()
ts_12h_ago = int((time.time() - (12 * 3600)) * 1000)
ts_72h_ago = int((time.time() - (72 * 3600)) * 1000)

calls_payload = [
    {
        "number": phone_fresh_12h,
        "call_type": CallEventType.INCOMING,
        "timestamp_ms": ts_12h_ago,
        "duration_sec": 30,
        "contact_name": "Fresh 12h Lead"
    },
    {
        "number": phone_stale_72h,
        "call_type": CallEventType.INCOMING,
        "timestamp_ms": ts_72h_ago,
        "duration_sec": 45,
        "contact_name": "Stale 72h Caller"
    }
]

res_auto = ingest_calls(device, calls_payload, manual_override=False)
print(f"  Auto-sync result (48h rolling window): {res_auto}")
assert res_auto["created"] == 1, f"Expected 1 created call, got {res_auto['created']}"
assert res_auto["new_leads"] == 1, f"Expected 1 new lead, got {res_auto['new_leads']}"
assert res_auto["skipped_stale"] == 1, f"Expected 1 stale call skipped (>48h), got {res_auto['skipped_stale']}"

# Verify DB
assert Lead.objects.filter(phone__endswith=phone_fresh_12h[-10:]).exists(), "Fresh 12h lead must be created"
assert not Lead.objects.filter(phone__endswith=phone_stale_72h[-10:]).exists(), "Stale 72h caller must NOT create a lead"

print("  ✓ Normal rolling auto-sync strictly enforces 48-hour horizon.")

# -------------------------------------------------------------------
# SUITE 2: Manual Historical Override
# -------------------------------------------------------------------
print("\n[Suite 2] Testing Manual Override for Historical Ingestion...")

phone_manual_72h = '9666600003'
phone_manual_30d = '9666600004'

Lead.objects.filter(phone__in=[phone_manual_72h, phone_manual_30d]).delete()
CallEvent.objects.filter(raw_number__in=[phone_manual_72h, phone_manual_30d]).delete()

ts_30d_ago = int((time.time() - (30 * 86400)) * 1000)

calls_manual_payload = [
    {
        "number": phone_manual_72h,
        "call_type": CallEventType.INCOMING,
        "timestamp_ms": ts_72h_ago,
        "duration_sec": 45,
        "contact_name": "Manual 72h Caller"
    },
    {
        "number": phone_manual_30d,
        "call_type": CallEventType.INCOMING,
        "timestamp_ms": ts_30d_ago,
        "duration_sec": 50,
        "contact_name": "Manual 30d Caller"
    }
]

# Run with manual_override=True
res_manual = ingest_calls(device, calls_manual_payload, manual_override=True)
print(f"  Manual override result: {res_manual}")
assert res_manual["created"] == 2, f"Expected 2 created calls with manual override, got {res_manual['created']}"
assert res_manual["skipped_stale"] == 0, f"Expected 0 skipped with manual override, got {res_manual['skipped_stale']}"

assert Lead.objects.filter(phone__endswith=phone_manual_72h[-10:]).exists(), "Manual 72h lead created"
assert Lead.objects.filter(phone__endswith=phone_manual_30d[-10:]).exists(), "Manual 30d lead created"

print("  ✓ Manual override successfully bypasses 48h limit and allows historical ingestion.")

# -------------------------------------------------------------------
# SUITE 3: Device-Level Settings & API Endpoint
# -------------------------------------------------------------------
print("\n[Suite 3] Testing Device Settings API Endpoint...")

client = Client()
client.force_login(admin)

resp_api = client.post(
    f'/calls/device/{device.pk}/update-sync-settings/',
    data=json.dumps({
        'allow_historical_sync': True,
        'sync_cutoff_date': (now - timedelta(days=10)).strftime('%Y-%m-%d')
    }),
    content_type='application/json'
)
assert resp_api.status_code == 200
data_api = resp_api.json()
assert data_api['success'] is True
assert data_api['allow_historical_sync'] is True

device.refresh_from_db()
assert device.allow_historical_sync is True
assert device.sync_cutoff_date == (now - timedelta(days=10)).date()

print("  ✓ Device settings API endpoint updated allow_historical_sync and sync_cutoff_date.")

# -------------------------------------------------------------------
# SUITE 4: Recording Upload 48-Hour Cutoff & Manual Override
# -------------------------------------------------------------------
print("\n[Suite 4] Testing Recording Upload 48-Hour Cutoff & Manual Override...")

dummy_audio = SimpleUploadedFile("test_call_48h.mp3", b"ID3" + b"\x00" * 1000, content_type="audio/mpeg")

# Reset device override to test 48h rejection
device.allow_historical_sync = False
device.sync_cutoff_date = None
device.save()

# Stale recording (72 hours ago) without override
stale_rec_time = (now - timedelta(hours=72)).isoformat()
rejected = False
try:
    save_recording(device, dummy_audio, {
        "device_file_id": "rec_stale_72h",
        "phone_number": "9555500001",
        "direction": "incoming",
        "duration_seconds": 60,
        "call_started_at": stale_rec_time
    }, manual_override=False)
except RecordingRejected as e:
    rejected = True
    print(f"  ✓ Stale 72h recording rejected without override: {e}")
assert rejected, "Recording older than 48 hours must be rejected in normal auto-sync"

# Stale recording with manual_override=True -> accepted
fresh_audio = SimpleUploadedFile("test_call_override.mp3", b"ID3" + b"\x00" * 1000, content_type="audio/mpeg")
rec, created = save_recording(device, fresh_audio, {
    "device_file_id": "rec_override_72h",
    "phone_number": "9555500002",
    "direction": "incoming",
    "duration_seconds": 60,
    "call_started_at": stale_rec_time
}, manual_override=True)
assert rec is not None
assert created is True
assert rec.match_status == 'UNMATCHED', "Recordings never create leads"
assert not Lead.objects.filter(phone__endswith="9555500002").exists(), "Recordings NEVER create leads"

print("  ✓ Recording upload 48-hour cutoff and manual override verified 100%.")

# Cleanup
Lead.objects.filter(phone__in=[phone_fresh_12h, phone_stale_72h, phone_manual_72h, phone_manual_30d, "9555500001", "9555500002"]).delete()
CallEvent.objects.filter(raw_number__in=[phone_fresh_12h, phone_stale_72h, phone_manual_72h, phone_manual_30d]).delete()
CallRecording.objects.filter(device_file_id__in=["rec_stale_72h", "rec_override_72h"]).delete()

print("\n" + "=" * 65)
print("ALL TRACK Y SUITES PASSED 100%!")
print("=" * 65)
