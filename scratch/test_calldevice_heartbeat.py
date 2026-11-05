import os
import sys

sys.path.insert(0, r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from datetime import timedelta
from django.utils import timezone
from django.test import Client
from accounts.models import User, UserRole
from calls.models import CallDevice

print("Testing CallSync Device Heartbeat & Connectivity Indicator...")

# 1. Fetch telecaller
tc = User.objects.filter(role=UserRole.TELECALLER).first()
if not tc:
    tc = User.objects.create(username="tc_callsync_test", role=UserRole.TELECALLER)
    tc.set_password("pass123")
    tc.save()

client = Client()
client.force_login(tc)

# 2. Test Heartbeat Ping Endpoint
device, _ = CallDevice.objects.get_or_create(user=tc)
res_ping = client.post('/calls/device/heartbeat/', data={'battery_percent': 78, 'is_charging': 'true', 'app_version': 'v2.4.0'})
assert res_ping.status_code == 200, f"Expected 200, got {res_ping.status_code}"
ping_data = res_ping.json()
assert ping_data['success'] is True
assert ping_data['battery_percent'] == 78
assert ping_data['is_charging'] is True
print("✅ Test 1 Passed: Heartbeat ping successfully updated battery and charging status")

# Verify device model properties
device.refresh_from_db()
assert device.battery_percent == 78
assert device.is_charging is True
assert device.is_online is True
print("✅ Test 2 Passed: Device is_online property is True when recently seen")

# 3. Test Desktop Status Query Endpoint
res_status = client.get('/calls/device-status/')
assert res_status.status_code == 200
status_data = res_status.json()
assert status_data['has_device'] is True
assert status_data['is_online'] is True
assert status_data['battery_percent'] == 78
assert status_data['is_charging'] is True
print("✅ Test 3 Passed: Desktop check_device_status returns live battery & connection state")

# 4. Test Stale / Asleep status when last seen 10 minutes ago
device.last_seen_at = timezone.now() - timedelta(minutes=10)
device.save(update_fields=['last_seen_at'])
device.refresh_from_db()
assert device.is_online is False

res_stale = client.get('/calls/device-status/')
stale_data = res_stale.json()
assert stale_data['is_online'] is False
print("✅ Test 4 Passed: Device correctly reported as offline when inactive for >120s")

# Restore device online state
device.last_seen_at = timezone.now()
device.save(update_fields=['last_seen_at'])

# 5. Test Telecaller UI HTML Rendering
res_ui = client.get('/telecaller/dashboard/')
assert res_ui.status_code == 200
content_html = res_ui.content.decode('utf-8')
assert 'tp-callsync-status-pill' in content_html, "CallSync status pill missing from telecaller navbar"
assert 'CallSync...' in content_html
print("✅ Test 5 Passed: CallSync status pill successfully rendered in telecaller navbar")

print("\n🎉 ALL CALLSYNC HEARTBEAT TESTS PASSED PERFECTLY!")
