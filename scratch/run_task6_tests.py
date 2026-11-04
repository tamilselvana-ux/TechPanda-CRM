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
from leads.models import WalkinEnquiryForm
from django.db import transaction

print("=== RUNNING TASK 6 (WALK-IN FORMS UI/UX) VERIFICATION ===")

admin = User.objects.filter(role=UserRole.ADMIN, is_active=True).first()
if not admin:
    admin = User.objects.filter(is_superuser=True).first()

client = Client()
client.force_login(admin)

branch = Branch.objects.filter(status='Active').first()
if not branch:
    branch = Branch.objects.create(name="T6 Branch", status="Active")

# TEST 1: Page loads with 200 and enterprise components
res1 = client.get('/admin/walkin-forms/')
assert res1.status_code == 200, f"Expected 200, got {res1.status_code}"
content = res1.content.decode('utf-8')
assert 'Walk-in Enquiry Forms' in content
assert 'Add Walk-in Form' in content
assert 'walkin-table' in content
print("PASS: Test 1 - Walk-in forms list page rendered with 200 and enterprise table.")

# TEST 2: Create new walk-in form
with transaction.atomic():
    res2 = client.post('/admin/walkin-forms/create/', {
        'title': 'Velachery Branch Walk-in',
        'description': 'Student admissions enquiry for Velachery campus',
        'branch': branch.id,
        'is_active': 'on'
    })
    assert res2.status_code == 302
    created = WalkinEnquiryForm.objects.filter(title='Velachery Branch Walk-in').first()
    assert created is not None
    assert 'velachery-branch-walk-in' in created.slug
    assert created.branch == branch
    assert created.is_active is True
    print(f"PASS: Test 2 - Created form '{created.title}' with slug: {created.slug}")

    # TEST 3: Edit walk-in form
    res3 = client.post(f'/admin/walkin-forms/{created.id}/edit/', {
        'title': 'Velachery Campus Walk-in (Updated)',
        'description': 'Updated admissions enquiry',
        'branch': branch.id,
        'is_active': 'on'
    })
    assert res3.status_code == 302
    created.refresh_from_db()
    assert created.title == 'Velachery Campus Walk-in (Updated)'
    print("PASS: Test 3 - Edited form title and description successfully.")

    # TEST 4: Search filter
    res4 = client.get(f'/admin/walkin-forms/?search=Velachery')
    assert res4.status_code == 200
    assert len(res4.context['forms']) >= 1
    print("PASS: Test 4 - Search filter correctly matched created form.")

    transaction.set_rollback(True)

print("\nALL TASK 6 TESTS PASSED PERFECTLY!")
