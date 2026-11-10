import os, sys, django
sys.path.insert(0, r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import time
from datetime import datetime, timedelta, timezone as dt_timezone
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone

from accounts.models import User
from calls.models import CallDevice, CallEvent, CallEventType
from calls.sync_services import ingest_calls, save_recording, RecordingRejected
from drive.models import CallRecording
from fb_leads.models import FacebookLead
from leads.models import Lead

print("=" * 60)
print("RUNNING TRACK X COMPREHENSIVE VERIFICATION SUITE")
print("=" * 60)

# Setup admin and telecaller test users
admin = User.objects.filter(is_superuser=True).first()
if not admin:
    admin = User.objects.filter(role='ADMIN').first()
assert admin is not None, "Admin user must exist"

telecaller = User.objects.filter(role='TELECALLER', is_active=True).first()
if not telecaller:
    telecaller = User.objects.create(
        username='test_tc_callsync',
        email='test_tc_callsync@test.com',
        role='TELECALLER',
        is_active=True
    )

device, _ = CallDevice.objects.get_or_create(user=telecaller)
device.sync_cutoff_date = None
device.save()

# -------------------------------------------------------------------
# SUITE 1: Facebook Leads Date Filtering
# -------------------------------------------------------------------
print("\n[Suite 1] Testing Facebook Leads date_from and date_to filtering...")
now = timezone.now()
today_str = now.strftime('%Y-%m-%d')
past_str = (now - timedelta(days=15)).strftime('%Y-%m-%d')

FacebookLead.objects.filter(leadgen_id__startswith='tst_fb_').delete()

fb1 = FacebookLead.objects.create(
    leadgen_id='tst_fb_today',
    full_name='FB Lead Today',
    phone='9876500001',
    created_on_facebook=now
)
fb2 = FacebookLead.objects.create(
    leadgen_id='tst_fb_past',
    full_name='FB Lead 15 Days Ago',
    phone='9876500002',
    created_on_facebook=now - timedelta(days=15)
)

client = Client()
client.force_login(admin)

# Filter date_from today
resp = client.get(f'/facebook-leads/?date_from={today_str}')
assert resp.status_code == 200
html = resp.content.decode()
assert 'FB Lead Today' in html, "Today's lead must be shown"
assert 'FB Lead 15 Days Ago' not in html, "15-day-old lead must be excluded when date_from=today"

# Filter date_to 15 days ago
resp2 = client.get(f'/facebook-leads/?date_to={past_str}')
assert resp2.status_code == 200
html2 = resp2.content.decode()
assert 'FB Lead 15 Days Ago' in html2, "15-day-old lead must be shown when date_to=past_str"
assert 'FB Lead Today' not in html2, "Today's lead must be excluded when date_to=past_str"

# API endpoint check
resp_api = client.get(f'/facebook-leads/api/recent/?date_from={today_str}')
assert resp_api.status_code == 200
api_data = resp_api.json()
api_names = [l['full_name'] for l in api_data['leads']]
assert 'FB Lead Today' in api_names
assert 'FB Lead 15 Days Ago' not in api_names

print("  ✓ Facebook leads listing and API date filters verified 100%.")

# -------------------------------------------------------------------
# SUITE 2: CallSync Ingestion Historical Cutoff Shield
# -------------------------------------------------------------------
print("\n[Suite 2] Testing CallSync call log historical age cutoff shield...")

phone_fresh = '9888800001'
phone_stale_35d = '9888800002'
phone_1year = '9888800003'

# Clean up any pre-existing leads
Lead.objects.filter(phone__in=[phone_fresh, phone_stale_35d, phone_1year]).delete()
CallEvent.objects.filter(raw_number__in=[phone_fresh, phone_stale_35d, phone_1year]).delete()

# Call 1: fresh call today (timestamp_ms = now)
fresh_ts = int(time.time() * 1000)
# Call 2: call from 45 days ago
stale_45d_ts = int((time.time() - (45 * 86400)) * 1000)
# Call 3: call from 1 year ago (365 days ago)
stale_1y_ts = int((time.time() - (365 * 86400)) * 1000)

calls_payload = [
    {
        "number": phone_fresh,
        "call_type": CallEventType.INCOMING,
        "timestamp_ms": fresh_ts,
        "duration_sec": 45,
        "contact_name": "Fresh Caller"
    },
    {
        "number": phone_stale_35d,
        "call_type": CallEventType.INCOMING,
        "timestamp_ms": stale_45d_ts,
        "duration_sec": 30,
        "contact_name": "Old 45d Caller"
    },
    {
        "number": phone_1year,
        "call_type": CallEventType.INCOMING,
        "timestamp_ms": stale_1y_ts,
        "duration_sec": 60,
        "contact_name": "1-Year-Old Caller"
    }
]

res = ingest_calls(device, calls_payload)
print(f"  Ingest result: {res}")
assert res["created"] == 1, f"Expected 1 created call, got {res['created']}"
assert res["new_leads"] == 1, f"Expected 1 new lead, got {res['new_leads']}"
assert res["skipped_stale"] == 2, f"Expected 2 stale calls skipped, got {res['skipped_stale']}"

# Verify database: Fresh lead was created
assert Lead.objects.filter(phone__endswith=phone_fresh[-10:]).exists(), "Fresh lead must exist"

# Verify database: 45d and 1-year calls were completely blocked and NEVER created leads!
assert not Lead.objects.filter(phone__endswith=phone_stale_35d[-10:]).exists(), "45d caller must NOT have created a lead!"
assert not Lead.objects.filter(phone__endswith=phone_1year[-10:]).exists(), "1-year caller must NOT have created a lead!"
assert not CallEvent.objects.filter(raw_number=phone_1year).exists(), "1-year caller must NOT have created a CallEvent!"

# Test device-level cutoff date
device.sync_cutoff_date = (now - timedelta(days=2)).date()
device.save()

phone_device_cutoff = '9888800004'
call_3d_ts = int((time.time() - (3 * 86400)) * 1000)
res_dev = ingest_calls(device, [{
    "number": phone_device_cutoff,
    "call_type": CallEventType.INCOMING,
    "timestamp_ms": call_3d_ts,
    "duration_sec": 20,
    "contact_name": "Device Cutoff Caller"
}])
assert res_dev["skipped_stale"] == 1, "Call older than device.sync_cutoff_date must be skipped"
assert not Lead.objects.filter(phone__endswith=phone_device_cutoff[-10:]).exists(), "No lead created for device cutoff caller"

print("  ✓ CallSync historical cutoff shield verified 100%. 1-year and stale calls are completely blocked.")

# -------------------------------------------------------------------
# SUITE 3: Call Recording Upload Protection & Cutoff Audit
# -------------------------------------------------------------------
print("\n[Suite 3] Testing Call Recording upload cutoff and lead protection...")

dummy_audio = SimpleUploadedFile("test_call.mp3", b"ID3" + b"\x00" * 1000, content_type="audio/mpeg")

# Test 3a: Recording older than 60 days is rejected
old_audio_time = (now - timedelta(days=90)).isoformat()
rejected = False
try:
    save_recording(device, dummy_audio, {
        "device_file_id": "rec_old_90d",
        "phone_number": "9777700001",
        "direction": "incoming",
        "duration_seconds": 60,
        "call_started_at": old_audio_time
    })
except RecordingRejected as e:
    rejected = True
    print(f"  ✓ Stale recording rejected as expected: {e}")
assert rejected, "Recording older than cutoff must raise RecordingRejected"

# Test 3b: Current recording for an unknown phone number NEVER creates a lead
unknown_phone = "9777700002"
Lead.objects.filter(phone__endswith=unknown_phone[-10:]).delete()

fresh_audio = SimpleUploadedFile("test_fresh.mp3", b"ID3" + b"\x00" * 1000, content_type="audio/mpeg")
rec, created = save_recording(device, fresh_audio, {
    "device_file_id": "rec_fresh_unknown",
    "phone_number": unknown_phone,
    "direction": "incoming",
    "duration_seconds": 35,
    "call_started_at": now.isoformat()
})
assert rec is not None
assert rec.lead is None, "Recording for unknown number must NOT have an attached lead"
assert rec.match_status == 'UNMATCHED', "Recording for unknown number must be marked UNMATCHED"
assert not Lead.objects.filter(phone__endswith=unknown_phone[-10:]).exists(), "Recordings must NEVER create leads in the CRM!"

print("  ✓ Call Recording upload protection verified 100%. Obsolete audio rejected, recordings never resurrect/create leads.")

# Clean up test artifacts
FacebookLead.objects.filter(leadgen_id__startswith='tst_fb_').delete()
Lead.objects.filter(phone__in=[phone_fresh, phone_stale_35d, phone_1year, phone_device_cutoff, unknown_phone]).delete()
CallRecording.objects.filter(device_file_id__in=["rec_old_90d", "rec_fresh_unknown"]).delete()

print("\n" + "=" * 60)
print("ALL SUITES PASSED! TRACK X FULLY VERIFIED.")
print("=" * 60)
