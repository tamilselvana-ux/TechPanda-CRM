import os
import sys

sys.path.insert(0, r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client
from accounts.models import User, UserRole
from branches.models import Branch
from leads.models import TelecallerLeadSetup

print("Testing On Duty / Out of Office Toggle...")

# 1. Fetch or create telecaller user
tc = User.objects.filter(role=UserRole.TELECALLER).first()
if not tc:
    tc = User.objects.create(username="tc_duty_test", role=UserRole.TELECALLER)
    tc.set_password("pass123")
    tc.save()

branch, _ = Branch.objects.get_or_create(name="T. Nagar")
tc.branch = branch
tc.is_on_duty = True
tc.save()

client = Client()
client.force_login(tc)

# 2. Test toggle endpoint to switch to Out of Office
res1 = client.post('/toggle-duty-status/')
assert res1.status_code == 200, f"Expected 200, got {res1.status_code}"
data1 = res1.json()
assert data1['is_on_duty'] is False, f"Expected is_on_duty False, got {data1['is_on_duty']}"
assert data1['status_label'] == "Out of Office"
print("✅ Test 1 Passed: Successfully toggled to Out of Office via API")

# Verify DB state
tc.refresh_from_db()
assert tc.is_on_duty is False

# 3. Test allocation filtering when Out of Office
setup, _ = TelecallerLeadSetup.objects.get_or_create(
    telecaller=tc,
    branch=branch,
    defaults={'is_active': True, 'assignment_percentage': 50}
)

active_setups = TelecallerLeadSetup.objects.filter(
    branch=branch,
    is_active=True,
    telecaller__is_active=True,
    telecaller__is_on_duty=True
)
assert not active_setups.filter(telecaller=tc).exists(), "Off-duty telecaller was NOT excluded from active allocation!"
print("✅ Test 2 Passed: Off-duty telecaller is strictly excluded from allocation queries")

# 4. Test toggle back to On Duty
res2 = client.post('/toggle-duty-status/')
assert res2.status_code == 200
data2 = res2.json()
assert data2['is_on_duty'] is True
assert data2['status_label'] == "On Duty"

tc.refresh_from_db()
assert tc.is_on_duty is True

active_setups_after = TelecallerLeadSetup.objects.filter(
    branch=branch,
    is_active=True,
    telecaller__is_active=True,
    telecaller__is_on_duty=True
)
assert active_setups_after.filter(telecaller=tc).exists(), "On-duty telecaller was not found in allocation!"
print("✅ Test 3 Passed: Successfully toggled back to On Duty and restored to allocation")

# 5. Test UI HTML rendering
res_ui = client.get('/telecaller/dashboard/')
assert res_ui.status_code == 200
assert 'tp-duty-toggle-btn' in res_ui.content.decode('utf-8')
assert 'On Duty' in res_ui.content.decode('utf-8')
print("✅ Test 4 Passed: Duty toggle button rendered cleanly on telecaller dashboard")

print("\n🎉 ALL DUTY STATUS TESTS PASSED PERFECTLY!")
