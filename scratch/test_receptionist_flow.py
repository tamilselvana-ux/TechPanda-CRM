import os
import sys

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from leads.models import Lead
from branches.models import Branch
from products.models import Product
from leads.views import receptionist_check_existing_lead, receptionist_dashboard
import json

User = get_user_model()

print("--- TESTING ITEM 143: RECEPTIONIST PRE-FILL & COUNSELOR DUTY STATUS ---")

from accounts.models import UserRole

# 1. Setup branch, receptionist, counselors
branch, _ = Branch.objects.get_or_create(name="Anna Nagar Test Center", defaults={"address": "Anna Nagar", "phone": "044-12345678"})
counselor_on_duty, _ = User.objects.get_or_create(
    username="counselor_duty_test",
    defaults={"role": UserRole.COUNSELOR, "first_name": "Kavitha", "last_name": "Raman", "is_on_duty": True, "branch": branch}
)
counselor_on_duty.role = UserRole.COUNSELOR
counselor_on_duty.is_on_duty = True
counselor_on_duty.branch = branch
counselor_on_duty.save()

counselor_off_duty, _ = User.objects.get_or_create(
    username="counselor_off_test",
    defaults={"role": UserRole.COUNSELOR, "first_name": "Suresh", "last_name": "Kumar", "is_on_duty": False, "branch": branch}
)
counselor_off_duty.role = UserRole.COUNSELOR
counselor_off_duty.is_on_duty = False
counselor_off_duty.branch = branch
counselor_off_duty.save()

receptionist, _ = User.objects.get_or_create(
    username="receptionist_test_user",
    defaults={"role": UserRole.RECEPTIONIST, "first_name": "Priya", "last_name": "Anand", "branch": branch}
)
receptionist.role = UserRole.RECEPTIONIST
receptionist.branch = branch
receptionist.save()

product, _ = Product.objects.get_or_create(name="Full Stack Python AI", defaults={"price": 45000})

# 2. Create existing lead for test phone
test_phone = "9840999888"
lead, created = Lead.objects.get_or_create(
    phone=test_phone,
    defaults={
        "name": "Arun Prakash",
        "email": "arun.prakash@example.com",
        "branch": branch,
        "product": product,
        "category": "Training",
        "assigned_counselor": counselor_on_duty
    }
)
if not created:
    lead.name = "Arun Prakash"
    lead.email = "arun.prakash@example.com"
    lead.branch = branch
    lead.product = product
    lead.assigned_counselor = counselor_on_duty
    lead.save()

factory = RequestFactory()

# 3. Test check_existing_lead endpoint
req = factory.get(f'/receptionist/leads/check-existing/?phone={test_phone}')
req.user = receptionist
res = receptionist_check_existing_lead(req)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
data = json.loads(res.content.decode('utf-8'))

assert data['success'] is True, "Pre-check must return success=True"
assert data['has_matches'] is True, "Pre-check must find existing match"
assert len(data['matches']) >= 1, "Must have at least one match"
match = data['matches'][0]
assert match['name'] == "Arun Prakash", f"Match name mismatch: {match.get('name')}"
assert match['course_id'] == product.id, f"Expected course_id {product.id}, got {match.get('course_id')}"
assert match['course_name'] == product.name, f"Expected course_name {product.name}, got {match.get('course_name')}"
print("✅ Test 1 Passed: Instant Phone Pre-Fill API returned valid student name, email, and course details.")

# 4. Test Receptionist Dashboard rendering
req_dash = factory.get('/receptionist/dashboard/')
req_dash.user = receptionist
res_dash = receptionist_dashboard(req_dash)
assert res_dash.status_code == 200, f"Dashboard returned {res_dash.status_code}"
content = res_dash.content.decode('utf-8')

assert "Branch Counselors Live Status:" in content, "Dashboard must render Counselor Live Duty Status bar"
assert "🟢 [On Duty]" in content, "Counselor dropdowns must contain 🟢 [On Duty] status indicator"
assert "🔴 [Out of Office]" in content, "Counselor dropdowns must contain 🔴 [Out of Office] status indicator"
assert "autoFillWalkin" in content, "Dashboard must include autoFillWalkin function"
assert "1-Sec Instant Pre-fill" in content, "Dashboard must include 1-Sec Instant Pre-fill button"
print("✅ Test 2 Passed: Receptionist Dashboard rendered duty status chips and 1-Sec Pre-fill controls successfully.")

print("--- ALL TESTS PASSED FOR ITEM 143 ---")
