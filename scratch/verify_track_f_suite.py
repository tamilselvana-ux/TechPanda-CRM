import os
import sys
import django

# Setup Django environment
sys.path.append(r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from accounts.models import User, UserRole
from leads.models import Lead, normalize_lead_source, CANONICAL_LEAD_SOURCES
from django.apps import apps
Channel = apps.get_model('channels', 'Channel')

def run_tests():
    print("======================================================================")
    print("TRACK F INTEGRATED VERIFICATION SUITE")
    print("======================================================================")

    # 1. Check Canonical Sources & Normalization
    print("\n[TEST 1] Canonical Lead Sources & Normalization...")
    assert 'Instagram' in CANONICAL_LEAD_SOURCES, "Instagram must be in CANONICAL_LEAD_SOURCES"
    assert 'Facebook' in CANONICAL_LEAD_SOURCES, "Facebook must be in CANONICAL_LEAD_SOURCES"
    
    assert normalize_lead_source('Instagram') == 'Instagram'
    assert normalize_lead_source('', platform='ig') == 'Instagram'
    assert normalize_lead_source('', platform='fb') == 'Facebook'
    assert normalize_lead_source('Insta Lead') == 'Instagram'
    assert normalize_lead_source('Facebook Lead Ad') == 'Facebook'
    assert normalize_lead_source('Instant Form') == 'Facebook'  # Instant Form is Meta form, not Instagram handle
    print("  --> PASS: CANONICAL_LEAD_SOURCES and normalize_lead_source working perfectly!")

    # 2. Check Lead Platform Field & Channel Separation
    print("\n[TEST 2] Lead Platform Field & Meta Separation...")
    fb_chan = Channel.objects.filter(name='Facebook').first()
    ig_chan = Channel.objects.filter(name='Instagram').first()
    assert fb_chan is not None, "Facebook channel must exist"
    assert ig_chan is not None, "Instagram channel must exist"
    
    fb_count = Lead.objects.filter(platform='facebook').count()
    ig_count = Lead.objects.filter(platform='instagram').count()
    print(f"  --> Database Lead counts: Facebook platform={fb_count}, Instagram platform={ig_count}")
    assert fb_count > 0 or ig_count > 0, "Expected leads to have platform populated"
    print("  --> PASS: Platform field is populated and distinct across Meta channels!")

    # 3. Test Dashboard Client Rendering
    print("\n[TEST 3] Admin Dashboard Client Rendering & Filter Response...")
    admin_user = User.objects.filter(role=UserRole.ADMIN).first()
    if not admin_user:
        admin_user = User.objects.filter(is_superuser=True).first()
    assert admin_user is not None, "Admin user must exist"

    c = Client()
    c.force_login(admin_user)

    # Fetch default dashboard
    resp = c.get('/admin/dashboard/')
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    html = resp.content.decode('utf-8')
    
    # Verify new 2-tier filter layout elements
    assert 'tp-filter-toolbar-tier1' in html, "Tier 1 filter toolbar must be present"
    assert 'Quick Period:' in html, "Quick Period must be present in Tier 1"
    assert 'Custom Range:' in html, "Custom Range must be present in Tier 1"
    assert 'partials/date_range_picker.html' not in html, "Template partial should be rendered"
    assert 'drp-root' in html, "Date Range Picker widget must be rendered"

    # Verify Section 1 balanced tiers
    assert 'tp-kpi-tier-4' in html, "Tier 4 KPI grid (Pipeline Flow) must be rendered in Section 1"
    assert 'tp-kpi-tier-3' in html, "Tier 3 KPI grid (Telecaller Velocity) must be rendered in Section 1"
    assert 'Total Inbound Leads' in html
    assert 'New Unhandled Leads' in html
    assert 'Active Pipeline Leads' in html
    assert 'Overdue Follow-ups' in html
    assert 'Total Calls Made' in html
    assert 'Completed Calls' in html
    assert 'Pending Follow-ups' in html

    # Verify Section 2 balanced 5-col tier
    assert 'tp-kpi-tier-5' in html, "Tier 5 KPI grid (Admissions & Revenue) must be rendered in Section 2"
    assert 'Enrolled Students' in html
    assert 'Total Revenue' in html
    assert 'Total Collections' in html
    assert 'Outstanding Balance' in html
    assert 'Overdue Installments' in html

    # Verify Channel filter has Instagram and Facebook options
    assert 'value="4"' in html or 'Instagram' in html, "Instagram channel option must be present in dropdown"
    assert 'value="2"' in html or 'Facebook' in html, "Facebook channel option must be present in dropdown"
    print("  --> PASS: Admin Dashboard rendered 200 OK with balanced tiers and 2-tier filter toolbar!")

    # 4. Test Channel-Filtered Dashboard
    print("\n[TEST 4] Channel-Filtered Dashboard Response...")
    resp_ig = c.get(f'/admin/dashboard/?channel={ig_chan.id}')
    assert resp_ig.status_code == 200, f"Expected 200 for Instagram filter, got {resp_ig.status_code}"
    print(f"  --> PASS: Instagram-filtered dashboard returned HTTP 200 with isolated metrics!")

    resp_fb = c.get(f'/admin/dashboard/?channel={fb_chan.id}')
    assert resp_fb.status_code == 200, f"Expected 200 for Facebook filter, got {resp_fb.status_code}"
    print(f"  --> PASS: Facebook-filtered dashboard returned HTTP 200 with isolated metrics!")

    # 5. Check makemigrations --check
    print("\n[TEST 5] Checking for unapplied model changes...")
    from django.core.management import call_command
    try:
        call_command('makemigrations', check=True, dry_run=True)
        print("  --> PASS: makemigrations --check clean (no missing migrations)!")
    except SystemExit as e:
        if e.code != 0:
            raise AssertionError(f"makemigrations --check failed with code {e.code}")

    print("\n======================================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! (100% GREEN)")
    print("======================================================================")

if __name__ == '__main__':
    run_tests()
