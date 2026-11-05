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
from calls.models import CallHistory
from leads.models_enrollment import Enrollment, PaymentTransaction
from leads.views_360 import lead_360_data
from leads.views import manager_leads_list
from accounts.models import UserRole
import json

User = get_user_model()

print("--- TESTING ITEM 145: UNIFIED 360° STUDENT SLIDE-OVER DRAWER ---")

# 1. Setup Data
branch, _ = Branch.objects.get_or_create(name="Anna Nagar 360 Center", defaults={"address": "Anna Nagar", "phone": "044-11112222"})
counselor, _ = User.objects.get_or_create(
    username="counselor_360_user",
    defaults={"role": UserRole.COUNSELOR, "first_name": "Divya", "last_name": "S", "branch": branch}
)
counselor.role = UserRole.COUNSELOR
counselor.branch = branch
counselor.save()

product, _ = Product.objects.get_or_create(name="Data Engineering Masterclass", defaults={"price": 60000})

lead, _ = Lead.objects.get_or_create(
    phone="9884011223",
    defaults={
        "name": "Karthik Raja",
        "email": "karthik.raja@example.com",
        "branch": branch,
        "product": product,
        "assigned_counselor": counselor
    }
)

# Create Call Session
call, _ = CallHistory.objects.get_or_create(
    lead=lead,
    caller=counselor,
    defaults={
        "call_status": "COMPLETED",
        "call_outcome": "Follow-Up Required",
        "duration": 185,
        "notes": "Discussed weekend batch timing. Highly interested in Python module."
    }
)

# Create Enrollment & Payment Transaction
enrollment, _ = Enrollment.objects.get_or_create(
    lead=lead,
    defaults={
        "enrollment_number": "ENR-360-TEST",
        "student_name": lead.name,
        "student_phone": lead.phone,
        "student_email": lead.email,
        "product": product,
        "payment_plan": "SPLIT_PAYMENT",
        "base_course_fee": 50000,
        "total_payable": 59000,
        "total_paid": 20000,
        "status": "Active"
    }
)

tx, _ = PaymentTransaction.objects.get_or_create(
    enrollment=enrollment,
    transaction_reference="UTR360TEST999",
    defaults={
        "amount": 20000,
        "payment_method": "UPI",
        "status": "Approved",
        "receipt_number": "REC-360-001"
    }
)

factory = RequestFactory()

# 2. Test 360 endpoint
req = factory.get(f'/leads/{lead.id}/360-data/')
req.user = counselor
res = lead_360_data(req, lead.id)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"

data = json.loads(res.content.decode('utf-8'))
assert data['success'] is True
assert data['student']['name'] == "Karthik Raja"
assert data['student']['enrollment_number'] == "ENR-360-TEST"
assert data['summary']['total_paid'] == 20000.0
assert data['summary']['balance_due'] == 39000.0
assert len(data['timeline']) >= 2, f"Expected at least 2 events (call + payment), got {len(data['timeline'])}"

types = [e['type'] for e in data['timeline']]
assert 'call' in types, "Timeline must include call session"
assert 'payment' in types, "Timeline must include payment transaction"
print("✅ Test 1 Passed: /leads/<id>/360-data/ API returned structured student details, fee summary, and multi-channel timeline.")

# 3. Test Drawer presence in Manager Leads page
sales_head, _ = User.objects.get_or_create(
    username="sh_360_test",
    defaults={"role": UserRole.SALES_HEAD, "branch": branch}
)
sales_head.role = UserRole.SALES_HEAD
sales_head.branch = branch
sales_head.save()

# Assign lead to sales head so row renders in table
lead.assigned_sales_head = sales_head
lead.save()

req_page = factory.get('/manager/leads/')
req_page.user = sales_head
res_page = manager_leads_list(req_page)
assert res_page.status_code == 200
html_page = res_page.content.decode('utf-8')

assert "student360Drawer" in html_page, "Base template must include student360Drawer component"
assert "student-360-drawer.js" in html_page, "Base template must include student-360-drawer.js script"
assert "data-open-360" in html_page, "Manager table must render 360° trigger button"
print("✅ Test 2 Passed: Student 360 Drawer component and triggers rendered successfully with HTTP 200.")

print("--- ALL TESTS PASSED FOR ITEM 145 ---")
