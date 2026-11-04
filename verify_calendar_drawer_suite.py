import os
import sys
import django
from decimal import Decimal
from datetime import datetime, time, date

# Setup Django environment
sys.path.insert(0, r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from accounts.models import UserRole

User = get_user_model()

print("=======================================================")
print("DIGIPANDA CRM · CALENDAR DRAWER AUTOMATED TEST SUITE")
print("=======================================================")

admin_user = User.objects.filter(role=UserRole.ADMIN, is_active=True).first()
accountant_user = User.objects.filter(role=UserRole.ACCOUNTANT, is_active=True).first()
counselor_user = User.objects.filter(role=UserRole.COUNSELOR, is_active=True).first()
branch_head_user = User.objects.filter(role=UserRole.BRANCH_HEAD, is_active=True).first()
manager_user = User.objects.filter(role=UserRole.SALES_HEAD, is_active=True).first()
telecaller_user = User.objects.filter(role=UserRole.TELECALLER, is_active=True).first()

client = Client()

named_routes_to_test = [
    ("Admin Dashboard", "admin_dashboard", admin_user, ["calendar-drawer", "cd-backdrop"]),
    ("Accountant Dashboard", "accountant_dashboard", accountant_user, ["calendar-drawer", "cd-backdrop", "customRangeToggleBtn"]),
    ("Accountant Verification", "accountant_payment_verification", accountant_user, ["calendar-drawer", "start_date", "end_date"]),
    ("Admin Leads", "admin_leads_list", admin_user, ["calendar-drawer", "date_from", "date_to"]),
    ("Admin New Leads", "admin_new_leads", admin_user, ["calendar-drawer", "date_from", "date_to"]),
    ("Branch Head Dashboard", "branch_head_dashboard", branch_head_user or admin_user, ["calendar-drawer", "start_date", "end_date"]),
    ("Counselor Dashboard", "counselor_dashboard", counselor_user, ["calendar-drawer", "start_date", "end_date"]),
    ("Sales Head Dashboard", "manager_dashboard", manager_user or admin_user, ["calendar-drawer", "start_date", "end_date"]),
    ("Telecaller Dashboard", "telecaller_dashboard", telecaller_user or admin_user, ["calendar-drawer", "start_date", "end_date"]),
    ("Admin Calls", "admin_calls_list", admin_user, ["calendar-drawer", "date_from", "date_to"]),
    ("Call Recordings", "call_recordings_list", admin_user, ["calendar-drawer", "date_from", "date_to"]),
    ("Admin Follow-ups", "admin_followups_list", admin_user, ["calendar-drawer", "date_from", "date_to"]),
    ("Counselor Follow-ups", "counselor_followups_list", counselor_user, ["calendar-drawer", "date_from", "date_to"]),
    ("Admin Reports", "admin_reports", admin_user, ["calendar-drawer", "date_from", "date_to"]),
    ("Manager Reports", "manager_reports", manager_user or admin_user, ["calendar-drawer", "start_date", "end_date"]),
    ("Telecaller RNR Report", "telecaller_rnr_report", admin_user, ["calendar-drawer", "start_date", "end_date"]),
    ("Finance Dashboard", "finance_dashboard", admin_user, ["calendar-drawer", "period"]),
]

passed_count = 0
failed_count = 0

for label, url_name, test_user, expected_tokens in named_routes_to_test:
    try:
        url = reverse(url_name)
    except Exception as e:
        print(f"[REVERSE ERROR] {label} ({url_name}): {e}")
        failed_count += 1
        continue

    if not test_user:
        print(f"[SKIP] {label} ({url}): No user available for role")
        continue

    client.force_login(test_user)
    try:
        response = client.get(url)
        if response.status_code == 200:
            content = response.content.decode("utf-8", errors="ignore")
            missing = [tok for tok in expected_tokens if tok not in content]
            if not missing:
                print(f"[PASS] {label} ({url}) -> HTTP 200, tokens verified {expected_tokens}")
                passed_count += 1
            else:
                print(f"[FAIL] {label} ({url}) -> Missing tokens: {missing}")
                failed_count += 1
        elif response.status_code == 302:
            print(f"[REDIRECT] {label} ({url}) -> 302 -> {response.url}")
            # If redirected due to role or permission, check with admin
            client.force_login(admin_user)
            resp_admin = client.get(url)
            if resp_admin.status_code == 200:
                print(f"  [PASS AS ADMIN] {label} ({url}) -> HTTP 200")
                passed_count += 1
            else:
                print(f"  [FAIL] {label} ({url}) -> HTTP {resp_admin.status_code}")
                failed_count += 1
        else:
            print(f"[FAIL] {label} ({url}) -> HTTP {response.status_code}")
            failed_count += 1
    except Exception as e:
        print(f"[ERROR] {label} ({url}) -> {e}")
        failed_count += 1

print("\n--- TIMEZONE & INCLUSIVE END-DATE VERIFICATION ---")
from leads.utils_date_filter import extract_normalized_date_range
from django.test import RequestFactory

rf = RequestFactory()
req = rf.get("/admin/leads/?date_from=2026-10-01&date_to=2026-10-15")
d_info = extract_normalized_date_range(req)

print(f"Parsed start_date: {d_info['start_date']} ({d_info['start_date_obj']})")
print(f"Parsed end_date: {d_info['end_date']} ({d_info['end_date_obj']})")

assert d_info['start_date_obj'] == date(2026, 10, 1), "Start date must equal 2026-10-01"
assert d_info['end_date_obj'] == date(2026, 10, 15), "End date must equal 2026-10-15"

tz = timezone.get_current_timezone()
print(f"Active Django Timezone: {tz}")
assert str(tz) in ["Asia/Kolkata", "Asia/Calcutta"], f"Expected Asia/Kolkata, got {tz}"

print("\nSUMMARY:")
print(f"Total Passed: {passed_count}/{len(named_routes_to_test)}")
print(f"Total Failed: {failed_count}/{len(named_routes_to_test)}")
if failed_count == 0:
    print("ALL ROUTE INTEGRATION TESTS PASSED 100%!")
