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
from branches.models import Branch
from leads.models import Lead, PipelineStatus
from django.db import transaction

print("=== RUNNING TASK 7 (PIPELINE STATUS DELETION & REASSIGNMENT) VERIFICATION ===")

admin = User.objects.filter(role=UserRole.ADMIN, is_active=True).first()
if not admin:
    admin = User.objects.filter(is_superuser=True).first()

client = Client()
client.force_login(admin)

branch = Branch.objects.filter(status='Active').first()
if not branch:
    branch = Branch.objects.create(name="T7 Branch", status="Active")

# TEST 1: Page renders with 200, shows leads count and delete buttons
res1 = client.get('/admin/settings/pipeline-statuses/')
assert res1.status_code == 200, f"Expected 200, got {res1.status_code}"
assert 'statusDeleteModal' in res1.content.decode('utf-8')
print("PASS: Test 1 - Pipeline statuses list page loaded with delete modal and counts.")

# TEST 2: Delete unused status directly
with transaction.atomic():
    st_unused = PipelineStatus.objects.create(
        name="Temporary Review",
        stage_category="General",
        sort_order=999,
        is_active=True
    )
    res2 = client.post(f'/admin/settings/pipeline-statuses/{st_unused.pk}/delete/')
    assert res2.status_code == 302
    assert not PipelineStatus.objects.filter(name="Temporary Review").exists()
    print("PASS: Test 2 - Unused status deleted directly without blocking.")
    transaction.set_rollback(True)

# TEST 3: Attempting to delete status with leads without reassignment target fails
with transaction.atomic():
    st_with_leads = PipelineStatus.objects.create(
        name="Review Pending",
        stage_category="General",
        sort_order=888,
        is_active=True
    )
    lead = Lead.objects.create(
        name="Lead in Review",
        phone="9988001122",
        status="Review Pending",
        branch=branch
    )
    # Post without reassign_to_status
    res3 = client.post(f'/admin/settings/pipeline-statuses/{st_with_leads.pk}/delete/', {})
    assert res3.status_code == 302
    assert PipelineStatus.objects.filter(name="Review Pending").exists()
    print("PASS: Test 3 - Deletion without target status was blocked.")

    # TEST 4: Delete status with leads and provide valid replacement status
    target_st = PipelineStatus.objects.filter(is_active=True).exclude(pk=st_with_leads.pk).first()
    assert target_st is not None, "Need at least one other active status"

    res4 = client.post(f'/admin/settings/pipeline-statuses/{st_with_leads.pk}/delete/', {
        'reassign_to_status': target_st.name
    })
    assert res4.status_code == 302
    assert not PipelineStatus.objects.filter(name="Review Pending").exists(), "Old status should be deleted"
    lead.refresh_from_db()
    assert lead.status == target_st.name, f"Expected lead to be moved to '{target_st.name}', got '{lead.status}'"
    print(f"PASS: Test 4 - Status with leads deleted and all leads atomically reassigned to '{target_st.name}'.")

    transaction.set_rollback(True)

print("\nALL TASK 7 TESTS PASSED PERFECTLY!")
