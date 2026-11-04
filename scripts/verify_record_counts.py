import os
import sys

base_dir = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM"
sys.path.insert(0, base_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.test.utils import setup_test_environment
setup_test_environment()

from django.test import Client
from accounts.models import User, UserRole
from leads.models import Lead, PaymentTransaction
from calls.models import CallHistory
from followups.models import FollowUp
from drive.models import CallRecording
from datetime import datetime, time
from django.utils import timezone

def verify_record_counts():
    print("=" * 70)
    print("DIGIPANDA CRM — RECORD COUNT EQUALITY TEST (COMPACT DATE PICKER)")
    print("=" * 70)

    admin = User.objects.filter(role=UserRole.ADMIN, is_active=True).first()
    client = Client()
    client.force_login(admin)

    d_start = "2026-10-01"
    d_end = "2026-10-25"
    s_dt = timezone.make_aware(datetime.combine(datetime.strptime(d_start, "%Y-%m-%d").date(), time.min))
    e_dt = timezone.make_aware(datetime.combine(datetime.strptime(d_end, "%Y-%m-%d").date(), time.max))

    # 1. Admin Leads List
    db_leads = Lead.objects.filter(created_at__range=(s_dt, e_dt)).count()
    res = client.get("/admin/leads/", {"date_from": d_start, "date_to": d_end, "view": "all"})
    view_leads = res.context["page_obj"].paginator.count
    assert db_leads == view_leads, f"Leads count mismatch: DB={db_leads}, View={view_leads}"
    print(f"[EQUALITY PASS] Admin Leads List: DB count ({db_leads}) == Filtered View count ({view_leads})")

    # 2. Admin New Leads Queue
    db_new = Lead.objects.filter(status="New", created_at__range=(s_dt, e_dt)).count()
    res = client.get("/admin/leads/new/", {"date_from": d_start, "date_to": d_end})
    view_new = res.context["page_obj"].paginator.count
    assert db_new == view_new, f"New Leads count mismatch: DB={db_new}, View={view_new}"
    print(f"[EQUALITY PASS] Admin New Leads Queue: DB count ({db_new}) == Filtered View count ({view_new})")

    # 3. Accountant Verification List
    db_payments = PaymentTransaction.objects.filter(payment_date__range=(s_dt, e_dt), status="PENDING_VERIFICATION").count()
    res = client.get("/accountant/verification/", {"start_date": d_start, "end_date": d_end, "status": "PENDING_VERIFICATION"})
    view_payments = res.context["page_obj"].paginator.count
    assert db_payments == view_payments, f"Payments count mismatch: DB={db_payments}, View={view_payments}"
    print(f"[EQUALITY PASS] Accountant Verification: DB count ({db_payments}) == Filtered View count ({view_payments})")

    # 4. Admin Calls List
    db_calls = CallHistory.objects.filter(call_started_at__range=(s_dt, e_dt)).count()
    res = client.get("/admin/calls/", {"date_from": d_start, "date_to": d_end})
    view_calls = res.context["page_obj"].paginator.count
    assert db_calls == view_calls, f"Calls count mismatch: DB={db_calls}, View={view_calls}"
    print(f"[EQUALITY PASS] Admin Calls List: DB count ({db_calls}) == Filtered View count ({view_calls})")

    # 5. Call Recordings List
    db_recs = CallRecording.objects.filter(recording_date__range=(s_dt, e_dt)).count()
    res = client.get("/call-recordings/recordings/", {"date_from": d_start, "date_to": d_end})
    view_recs = res.context["page_obj"].paginator.count
    assert db_recs == view_recs, f"Recordings count mismatch: DB={db_recs}, View={view_recs}"
    print(f"[EQUALITY PASS] Call Recordings List: DB count ({db_recs}) == Filtered View count ({view_recs})")

    # 6. Admin Followups List
    db_followups = FollowUp.objects.filter(follow_up_date__range=(s_dt.date(), e_dt.date())).count()
    res = client.get("/admin/followups/", {"date_from": d_start, "date_to": d_end})
    view_followups = res.context["page_obj"].paginator.count
    assert db_followups == view_followups, f"Followups count mismatch: DB={db_followups}, View={view_followups}"
    print(f"[EQUALITY PASS] Admin Followups List: DB count ({db_followups}) == Filtered View count ({view_followups})")

    print("\nALL RECORD COUNTS STRICTLY IDENTICAL (100% EQUALITY)")

if __name__ == "__main__":
    verify_record_counts()
