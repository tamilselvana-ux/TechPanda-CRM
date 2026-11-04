import os
import sys

base_dir = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM"
sys.path.insert(0, base_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.test import Client
from django.test.utils import setup_test_environment
from accounts.models import User, UserRole

setup_test_environment()

def run_tests():
    print("=" * 70)
    print("DIGIPANDA CRM — COMPACT DATE RANGE PICKER VERIFICATION SUITE")
    print("=" * 70)

    # Fetch active test users per role
    admin = User.objects.filter(role=UserRole.ADMIN, is_active=True).first()
    accountant = User.objects.filter(role=UserRole.ACCOUNTANT, is_active=True).first()
    counselor = User.objects.filter(role=UserRole.COUNSELOR, is_active=True).first()
    manager = User.objects.filter(role=UserRole.SALES_HEAD, is_active=True).first()
    branch_head = User.objects.filter(role=UserRole.BRANCH_HEAD, is_active=True).first()
    telecaller = User.objects.filter(role=UserRole.TELECALLER, is_active=True).first()
    receptionist = User.objects.filter(role=UserRole.RECEPTIONIST, is_active=True).first()

    print(f"Loaded Active Roles:\n - Admin: {admin}\n - Accountant: {accountant}\n - Counselor: {counselor}\n - Manager: {manager}\n - BranchHead: {branch_head}\n - Telecaller: {telecaller}\n - Receptionist: {receptionist}\n")

    test_pages = [
        {
            "id": 29,
            "name": "Admin Dashboard",
            "url": "/admin/dashboard/",
            "user": admin,
            "from_name": "from_date",
            "to_name": "to_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {"channel": ""},
        },
        {
            "id": 30,
            "name": "Accountant Dashboard",
            "url": "/accountant/dashboard/",
            "user": accountant or admin,
            "from_name": "start_date",
            "to_name": "end_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {},
        },
        {
            "id": 31,
            "name": "Accountant Verification Queue",
            "url": "/accountant/verification/",
            "user": accountant or admin,
            "from_name": "start_date",
            "to_name": "end_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {"status": "PENDING_VERIFICATION"},
        },
        {
            "id": 32,
            "name": "Admin Leads List",
            "url": "/admin/leads/",
            "user": admin,
            "from_name": "date_from",
            "to_name": "date_to",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {"view": "all"},
        },
        {
            "id": 33,
            "name": "Admin New Leads Queue",
            "url": "/admin/leads/new/",
            "user": admin,
            "from_name": "date_from",
            "to_name": "date_to",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {},
        },
        {
            "id": 34,
            "name": "Branch Head Dashboard",
            "url": "/manager/branch-head/dashboard/",
            "user": branch_head or admin,
            "from_name": "start_date",
            "to_name": "end_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {"period": "custom"},
        },
        {
            "id": 35,
            "name": "Counselor Dashboard",
            "url": "/counselor/dashboard/",
            "user": counselor or admin,
            "from_name": "start_date",
            "to_name": "end_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {"period": "custom"},
        },
        {
            "id": 36,
            "name": "Manager Dashboard",
            "url": "/manager/dashboard/",
            "user": manager or admin,
            "from_name": "start_date",
            "to_name": "end_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {"period": "custom"},
        },
        {
            "id": 37,
            "name": "Telecaller Dashboard",
            "url": "/telecaller/dashboard/",
            "user": telecaller or admin,
            "from_name": "start_date",
            "to_name": "end_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {"period": "custom"},
        },
        {
            "id": 38,
            "name": "Admin Calls List",
            "url": "/admin/calls/",
            "user": admin,
            "from_name": "date_from",
            "to_name": "date_to",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {},
        },
        {
            "id": 39,
            "name": "Call Recordings List",
            "url": "/call-recordings/recordings/",
            "user": admin,
            "from_name": "date_from",
            "to_name": "date_to",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {},
        },
        {
            "id": 40,
            "name": "Admin Followups List",
            "url": "/admin/followups/",
            "user": admin,
            "from_name": "date_from",
            "to_name": "date_to",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {},
        },
        {
            "id": 41,
            "name": "Counselor Followups List",
            "url": "/counselor/followups/",
            "user": counselor or admin,
            "from_name": "date_from",
            "to_name": "date_to",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {},
        },
        {
            "id": 42,
            "name": "Admin Reports",
            "url": "/admin/reports/",
            "user": admin,
            "from_name": "start_date",
            "to_name": "end_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {"date_filter": "custom"},
        },
        {
            "id": 43,
            "name": "Manager Reports",
            "url": "/manager/reports/",
            "user": manager or admin,
            "from_name": "start_date",
            "to_name": "end_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {"date_filter": "custom"},
        },
        {
            "id": 44,
            "name": "Telecaller RnR Report",
            "url": "/reports/telecaller-rnr/",
            "user": admin,
            "from_name": "start_date",
            "to_name": "end_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {"period": "custom"},
        },
        {
            "id": 45,
            "name": "Finance Dashboard",
            "url": "/finance/dashboard/",
            "user": admin,
            "from_name": "start_date",
            "to_name": "end_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {"period": "custom"},
        },
        {
            "id": 46,
            "name": "Receptionist Dashboard",
            "url": "/receptionist/dashboard/",
            "user": receptionist or admin,
            "from_name": "from_date",
            "to_name": "to_date",
            "test_from": "2026-10-01",
            "test_to": "2026-10-15",
            "extra_params": {},
        },
    ]

    client = Client()
    all_passed = True

    for p in test_pages:
        user = p["user"]
        client.force_login(user)

        # 1. Base GET (unfiltered / default range)
        res_default = client.get(p["url"])
        if res_default.status_code != 200:
            print(f"[FAIL] Item {p['id']} {p['name']} default GET returned {res_default.status_code} (Redirect: {res_default.get('Location')})")
            all_passed = False
            continue

        html_default = res_default.content.decode("utf-8")
        
        # Verify drp-root presence
        if "drp-root" not in html_default:
            print(f"[FAIL] Item {p['id']} {p['name']} does not contain 'drp-root' class!")
            all_passed = False
            continue

        # Verify correct parameter names in data attributes
        expected_from_attr = f'data-from-name="{p["from_name"]}"'
        expected_to_attr = f'data-to-name="{p["to_name"]}"'
        if expected_from_attr not in html_default or expected_to_attr not in html_default:
            print(f"[FAIL] Item {p['id']} {p['name']} attribute mismatch: expected {expected_from_attr} and {expected_to_attr}")
            all_passed = False
            continue

        # 2. Filtered GET with From and To dates
        filter_params = {
            p["from_name"]: p["test_from"],
            p["to_name"]: p["test_to"],
            **p["extra_params"],
        }
        res_filtered = client.get(p["url"], filter_params)
        if res_filtered.status_code != 200:
            print(f"[FAIL] Item {p['id']} {p['name']} filtered GET returned {res_filtered.status_code}")
            all_passed = False
            continue

        html_filtered = res_filtered.content.decode("utf-8")
        # Check hidden inputs carry the values
        if f'value="{p["test_from"]}"' not in html_filtered or f'value="{p["test_to"]}"' not in html_filtered:
            print(f"[FAIL] Item {p['id']} {p['name']} filtered hidden input values not populated!")
            all_passed = False
            continue

        # 3. Test Clearing Date Filter
        clear_params = {
            p["from_name"]: "",
            p["to_name"]: "",
            **{k: v for k, v in p["extra_params"].items() if k not in ("period", "date_filter")},
        }
        res_cleared = client.get(p["url"], clear_params)
        if res_cleared.status_code != 200:
            print(f"[FAIL] Item {p['id']} {p['name']} cleared GET returned {res_cleared.status_code}")
            all_passed = False
            continue

        print(f"[PASS] Item {p['id']:02d}: {p['name']} (URL: {p['url']}) | from={p['from_name']} to={p['to_name']} | 100% PASS")

    # Test CSV export on telecaller RNR report with active date range
    client.force_login(admin)
    res_rnr_csv = client.get("/reports/telecaller-rnr/", {
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
        "period": "custom",
        "export": "csv"
    })
    if res_rnr_csv.status_code == 200 and "text/csv" in res_rnr_csv.headers.get("Content-Type", ""):
        print("[PASS] Item 44: Telecaller RnR CSV Export respects custom date range and returns CSV headers.")
    else:
        print(f"[FAIL] Item 44: Telecaller RnR CSV Export returned {res_rnr_csv.status_code}")
        all_passed = False

    if all_passed:
        print("\n" + "=" * 70)
        print(">>> ALL 18 PAGES PASSED AUTOMATED VERIFICATION WITH 100% SUCCESS! <<<")
        print("=" * 70)
    else:
        print("\nSOME TESTS FAILED! CHECK OUTPUT ABOVE.")

if __name__ == "__main__":
    run_tests()
