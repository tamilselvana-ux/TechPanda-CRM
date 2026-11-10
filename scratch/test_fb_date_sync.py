import os
import sys
import datetime
from unittest.mock import patch, MagicMock

sys.path.insert(0, r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.test import RequestFactory, Client
from django.utils import timezone
from accounts.models import User
from branches.models import Branch
from fb_leads.models import FacebookAccount, FacebookPage, FacebookLead
from fb_leads.facebook import _to_timestamp, sync_page_leads, sync_all_leads
from fb_leads.views import _parse_sync_time_range, sync_leads, fb_page_sync, fb_page_update_cutoff
from fb_leads.scheduler import run_auto_sync_cycle, trigger_immediate_page_sync

def test_to_timestamp_helper():
    print("Testing 1: _to_timestamp helper...")
    # Test date object
    d = datetime.date(2026, 11, 1)
    ts_start = _to_timestamp(d, is_end_of_day=False)
    ts_end = _to_timestamp(d, is_end_of_day=True)
    assert ts_start < ts_end, "Start of day timestamp must be < end of day"
    
    # Test string date
    ts_str = _to_timestamp("2026-11-01", is_end_of_day=False)
    assert ts_str == ts_start, "String YYYY-MM-DD should yield identical timestamp"

    # Test int/float timestamp
    assert _to_timestamp(1730419200) == 1730419200
    assert _to_timestamp(None) is None
    print("  [PASS] _to_timestamp helper handles date, string, timestamp, None")

def test_date_filtered_sync():
    print("Testing 2: sync_page_leads date filtering...")
    # Clean up previous test leads
    FacebookLead.objects.filter(leadgen_id__startswith="lead_").delete()
    # Setup dummy account and page
    acc, _ = FacebookAccount.objects.get_or_create(account_name="Test Account", defaults={"access_token": "mock_token"})
    page, _ = FacebookPage.objects.get_or_create(
        page_id="page_mock_123",
        account=acc,
        defaults={"page_name": "Test Page", "page_access_token": "page_token_123"}
    )

    # Mock Graph API responses
    mock_forms = {"data": [{"id": "form_999", "name": "Admissions Form 2026"}]}
    
    # 3 leads: one from today (Nov 9), one from 3 days ago (Nov 6), one from 1 year ago (Nov 2025)
    now = timezone.now()
    lead_today = {
        "id": "lead_today_001",
        "created_time": now.strftime("%Y-%m-%dT%H:%M:%S+0000"),
        "field_data": [{"name": "full_name", "values": ["Alice Today"]}, {"name": "phone_number", "values": ["9876540001"]}]
    }
    lead_3d = {
        "id": "lead_3d_002",
        "created_time": (now - datetime.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S+0000"),
        "field_data": [{"name": "full_name", "values": ["Bob 3DaysAgo"]}, {"name": "phone_number", "values": ["9876540002"]}]
    }
    lead_old = {
        "id": "lead_old_003",
        "created_time": "2025-01-15T10:00:00+0000",
        "field_data": [{"name": "full_name", "values": ["Old Deleted Candidate"]}, {"name": "phone_number", "values": ["9876540003"]}]
    }

    mock_leads_page = {
        "data": [lead_today, lead_3d, lead_old],
        "paging": {}
    }

    def mock_get(path, params=None, token=None, **kwargs):
        if "leadgen_forms" in path:
            return mock_forms
        if "leads" in path:
            return mock_leads_page
        return {}

    with patch("fb_leads.facebook._get", side_effect=mock_get):
        # A: Sync with since = today only -> should only import lead_today
        today_start = timezone.make_aware(datetime.datetime.combine(now.date(), datetime.time.min), timezone.get_current_timezone())
        new_cnt = sync_page_leads("page_mock_123", since=today_start)
        assert FacebookLead.objects.filter(leadgen_id="lead_today_001").exists()
        assert not FacebookLead.objects.filter(leadgen_id="lead_3d_002").exists(), "Lead from 3 days ago should have been skipped"
        assert not FacebookLead.objects.filter(leadgen_id="lead_old_003").exists(), "1-year old lead should have been skipped"
        print("  [PASS] sync_page_leads with since=today imported only today's lead and skipped older ones")

        # B: Sync with cutoff date
        page.sync_cutoff_date = (now - datetime.timedelta(days=5)).date()
        page.save()
        # Even with since=None, the page cutoff should block the 1-year old lead
        new_cnt2 = sync_page_leads("page_mock_123", since=None)
        assert FacebookLead.objects.filter(leadgen_id="lead_3d_002").exists(), "Lead from 3 days ago should be imported (within cutoff)"
        assert not FacebookLead.objects.filter(leadgen_id="lead_old_003").exists(), "1-year old lead MUST remain blocked by cutoff"
        print("  [PASS] Page cutoff date successfully shielded database from 1-year old lead")

def test_view_parameters():
    print("Testing 3: View time range parser and cutoff update view...")
    factory = RequestFactory()
    
    # Test today
    req = factory.post("/fake/", {"sync_mode": "today"})
    since, until, label = _parse_sync_time_range(req)
    assert label == "Today"
    assert since is not None
    assert until is None

    # Test 7 days
    req = factory.post("/fake/", {"sync_mode": "7days"})
    since, until, label = _parse_sync_time_range(req)
    assert label == "Last 7 Days"

    # Test custom range
    req = factory.post("/fake/", {"sync_mode": "custom", "start_date": "2026-11-01", "end_date": "2026-11-08"})
    since, until, label = _parse_sync_time_range(req)
    assert label == "2026-11-01 to 2026-11-08"
    assert since is not None and until is not None
    print("  [PASS] _parse_sync_time_range correctly parses all sync modes")

    # Test updating cutoff date via fb_page_update_cutoff
    user = User.objects.filter(is_superuser=True).first() or User.objects.filter(role__in=["ADMIN", "superadmin"]).first()
    page = FacebookPage.objects.filter(page_id="page_mock_123").first()
    
    req_cutoff = factory.post(f"/facebook-leads/pages/{page.id}/cutoff/", {"sync_cutoff_date": "2026-11-01"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    req_cutoff.user = user
    resp = fb_page_update_cutoff(req_cutoff, page.id)
    assert resp.status_code == 200
    page.refresh_from_db()
    assert str(page.sync_cutoff_date) == "2026-11-01"
    print("  [PASS] fb_page_update_cutoff updated page.sync_cutoff_date to 2026-11-01")

def test_ui_rendering():
    print("Testing 4: Template rendering of Sync Modal and Cutoff column...")
    client = Client()
    user = User.objects.filter(is_superuser=True).first() or User.objects.filter(role__in=["ADMIN", "superadmin"]).first()
    client.force_login(user)

    resp_leads = client.get("/facebook-leads/")
    assert resp_leads.status_code == 200
    assert "syncLeadsModal" in resp_leads.content.decode("utf-8")
    assert "Today Only" in resp_leads.content.decode("utf-8")
    assert "Custom Date Range" in resp_leads.content.decode("utf-8")
    print("  [PASS] /facebook-leads/ renders Sync Leads modal with all date options")

    resp_acc = client.get("/facebook-leads/accounts/")
    assert resp_acc.status_code == 200
    assert "Sync Cutoff Date" in resp_acc.content.decode("utf-8")
    assert "cutoffDate-" in resp_acc.content.decode("utf-8")
    print("  [PASS] /facebook-leads/accounts/ renders Sync Cutoff Date column and inputs")

if __name__ == "__main__":
    test_to_timestamp_helper()
    test_date_filtered_sync()
    test_view_parameters()
    test_ui_rendering()
    print("\nALL FACEBOOK DATE-FILTER TESTS PASSED 100%!")
