import os
import sys

sys.path.insert(0, r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test.utils import setup_test_environment
setup_test_environment()

from django.test import Client
from accounts.models import User, UserRole

print("=== RUNNING TASK 3 (ACCOUNTANT DASHBOARD CUSTOM DATES) VERIFICATION ===")

accountant = User.objects.filter(role=UserRole.ACCOUNTANT, is_active=True).first()
if not accountant:
    accountant = User.objects.filter(is_superuser=True).first()

client = Client()
client.force_login(accountant)

# TEST 1: Default to current month
res1 = client.get('/accountant/dashboard/')
assert res1.status_code == 200, f"Expected 200, got {res1.status_code}"
assert 'showing_range_label' in res1.context, "showing_range_label missing from context"
print(f"PASS: Test 1 - Default range: {res1.context['showing_range_label']}")

# TEST 2: Custom date query ?from=2026-10-01&to=2026-10-25
res2 = client.get('/accountant/dashboard/?from=2026-10-01&to=2026-10-25')
assert res2.status_code == 200, f"Expected 200, got {res2.status_code}"
assert res2.context['start_date'] == '2026-10-01'
assert res2.context['end_date'] == '2026-10-25'
assert 'Showing: 01 Oct 2026 – 25 Oct 2026' in res2.context['showing_range_label']
print(f"PASS: Test 2 - Custom query ?from=...&to=... correctly parsed: {res2.context['showing_range_label']}")

# TEST 3: Preset This Financial Year ?period=fy
res3 = client.get('/accountant/dashboard/?period=fy')
assert res3.status_code == 200
assert res3.context['start_date'].endswith('-04-01'), f"FY start must be April 1, got {res3.context['start_date']}"
print(f"PASS: Test 3 - Financial Year preset: {res3.context['showing_range_label']}")

# TEST 4: Invalid range from > to resets gracefully without crashing
res4 = client.get('/accountant/dashboard/?from=2026-10-30&to=2026-10-01')
assert res4.status_code == 200, "Invalid date range caused crash!"
assert res4.context['start_date'] <= res4.context['end_date'], "Dates not normalized on invalid range!"
print(f"PASS: Test 4 - Invalid date range gracefully warned and reset without crashing.")

print("\nALL TASK 3 TESTS PASSED PERFECTLY!")
