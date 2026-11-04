import os
import sys
import django

# Setup Django environment
sys.path.insert(0, r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test.utils import setup_test_environment
setup_test_environment()

from django.test import Client
from django.contrib.auth import get_user_model
from accounts.models import UserRole

User = get_user_model()

print("=======================================================")
print("DIGIPANDA CRM · KPI DRILLDOWN & EQUALITY TEST SUITE")
print("=======================================================")

admin_user = User.objects.filter(role=UserRole.ADMIN, is_active=True).first()
branch_head_user = User.objects.filter(role=UserRole.BRANCH_HEAD, is_active=True).first()
counselor_user = User.objects.filter(role=UserRole.COUNSELOR, is_active=True).first()

client = Client()

passed = 0
failed = 0

def get_context_dict(response):
    d = {}
    if response.context:
        for sub in response.context:
            if hasattr(sub, 'flatten'):
                d.update(sub.flatten())
            elif isinstance(sub, dict):
                d.update(sub)
    return d

# Test 1: Admin Dashboard & Drilldowns
if admin_user:
    client.force_login(admin_user)
    r_dash = client.get("/admin/dashboard/")
    if r_dash.status_code == 200:
        ctx = get_context_dict(r_dash)
        dash_total = ctx.get('total_leads', 0)
        dash_new = ctx.get('new_leads', 0)
        print(f"Admin Dashboard Metrics: Total={dash_total}, New={dash_new}")

        # Drilldown Total Leads
        r_total = client.get("/admin/leads/?view=all")
        ctx_tot = get_context_dict(r_total)
        list_total = ctx_tot['page_obj'].paginator.count if 'page_obj' in ctx_tot else None
        print(f"  Drilldown Total: Dash={dash_total} vs Listing={list_total}")
        if dash_total == list_total:
            print("  [PASS] Total Leads count equality verified")
            passed += 1
        else:
            print("  [FAIL] Total Leads count mismatch")
            failed += 1

        # Drilldown New Leads
        r_new = client.get("/admin/leads/?status=New")
        ctx_new = get_context_dict(r_new)
        list_new = ctx_new['page_obj'].paginator.count if 'page_obj' in ctx_new else None
        print(f"  Drilldown New: Dash={dash_new} vs Listing={list_new}")
        if dash_new == list_new:
            print("  [PASS] New Leads count equality verified")
            passed += 1
        else:
            print("  [FAIL] New Leads count mismatch")
            failed += 1

# Test 2: Branch Head Dashboard & Drilldowns
if branch_head_user:
    client.force_login(branch_head_user)
    r_bh = client.get("/manager/branch-head/dashboard/")
    if r_bh.status_code == 200:
        ctx = get_context_dict(r_bh)
        bh_total = ctx.get('branch_leads_count', 0)
        bh_attended = ctx.get('attended_leads_count', 0)
        print(f"\nBranch Head Metrics: Total={bh_total}, Attended={bh_attended}")

        # Drilldown Total Branch Leads
        r_bht = client.get("/manager/branch-head/leads/")
        ctx_bht = get_context_dict(r_bht)
        bht_list = ctx_bht['page_obj'].paginator.count if 'page_obj' in ctx_bht else None
        print(f"  Drilldown BH Total: Dash={bh_total} vs Listing={bht_list}")
        if bh_total == bht_list:
            print("  [PASS] Branch Head Total Leads equality verified")
            passed += 1
        else:
            print("  [FAIL] Branch Head Total Leads count mismatch")
            failed += 1

        # Drilldown Attended
        r_bha = client.get("/manager/branch-head/leads/?status_group=attended")
        ctx_bha = get_context_dict(r_bha)
        bha_list = ctx_bha['page_obj'].paginator.count if 'page_obj' in ctx_bha else None
        print(f"  Drilldown BH Attended: Dash={bh_attended} vs Listing={bha_list}")
        if bh_attended == bha_list:
            print("  [PASS] Branch Head Attended Leads equality verified")
            passed += 1
        else:
            print("  [FAIL] Branch Head Attended count mismatch")
            failed += 1

# Test 3: Counselor Dashboard & Drilldowns
if counselor_user:
    client.force_login(counselor_user)
    r_cd = client.get("/counselor/dashboard/")
    if r_cd.status_code == 200:
        ctx = get_context_dict(r_cd)
        c_leads = ctx.get('my_leads_count', 0)
        c_visits = ctx.get('visits_count', 0)
        print(f"\nCounselor Metrics: My Leads={c_leads}, Visits={c_visits}")

        # Drilldown My Leads
        r_cl = client.get("/counselor/leads/")
        ctx_cl = get_context_dict(r_cl)
        cl_list = ctx_cl['page_obj'].paginator.count if 'page_obj' in ctx_cl else None
        print(f"  Drilldown Counselor Leads: Dash={c_leads} vs Listing={cl_list}")
        if c_leads == cl_list:
            print("  [PASS] Counselor My Leads equality verified")
            passed += 1
        else:
            print("  [FAIL] Counselor My Leads count mismatch")
            failed += 1

        # Drilldown Visits
        r_cv = client.get("/counselor/leads/?status=Visited")
        ctx_cv = get_context_dict(r_cv)
        cv_list = ctx_cv['page_obj'].paginator.count if 'page_obj' in ctx_cv else None
        print(f"  Drilldown Counselor Visits: Dash={c_visits} vs Listing={cv_list}")
        if c_visits == cv_list:
            print("  [PASS] Counselor Visits equality verified")
            passed += 1
        else:
            print("  [FAIL] Counselor Visits count mismatch")
            failed += 1

print("\n=======================================================")
print(f"RESULTS: Passed={passed}, Failed={failed}")
if failed == 0:
    print("ALL KPI EQUALITY & DRILLDOWN TESTS PASSED 100%!")
print("=======================================================")
