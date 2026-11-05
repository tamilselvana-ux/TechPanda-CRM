import os
import sys

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from decimal import Decimal
from leads.models import Lead
from branches.models import Branch
from products.models import Product
from leads.models_enrollment import Enrollment, Installment
from leads.services_enrollment import _setup_manual_installments
from leads.views_enrollment import enrollment_create_or_edit
from accounts.models import UserRole

User = get_user_model()

print("--- TESTING ITEM 146: DYNAMIC INSTALLMENT BALANCING SLIDER ---")

# 1. Setup Data
branch, _ = Branch.objects.get_or_create(name="Slider Test Center", defaults={"address": "Slider Ave", "phone": "044-77778888"})
counselor, _ = User.objects.get_or_create(
    username="counselor_slider_test",
    defaults={"role": UserRole.COUNSELOR, "first_name": "Rohan", "last_name": "Sharma", "branch": branch}
)
counselor.role = UserRole.COUNSELOR
counselor.branch = branch
counselor.save()

product, _ = Product.objects.get_or_create(name="Cloud DevOps Pro", defaults={"price": 50000})

lead, _ = Lead.objects.get_or_create(
    phone="9871122334",
    defaults={
        "name": "Siddharth Verma",
        "email": "siddharth@example.com",
        "branch": branch,
        "product": product,
        "assigned_counselor": counselor
    }
)
lead.assigned_counselor = counselor
lead.branch = branch
lead.save()

# 2. Test manual installment auto-balancing math:
# Total 59,000 (50,000 + 18% GST).
# 3 Custom installments:
# Inst #1 (Down payment today): 25,000
# Inst #2: 20,000
# Inst #3 (Remainder absorbed): 14,000
enrollment, _ = Enrollment.objects.get_or_create(
    lead=lead,
    defaults={
        "enrollment_number": "ENR-SLIDER-001",
        "student_name": lead.name,
        "student_phone": lead.phone,
        "student_email": lead.email,
        "product": product,
        "payment_plan": "SPLIT_PAYMENT",
        "installment_method": "MANUAL",
        "base_course_fee": 50000,
        "total_payable": 59000,
        "total_paid": 0,
        "status": "Active"
    }
)

custom_data = [
    {"number": 1, "amount": "25000.00", "due_date": "2026-11-05"},
    {"number": 2, "amount": "20000.00", "due_date": "2026-12-05"},
    {"number": 3, "amount": "14000.00", "due_date": "2027-01-05"},
]

_setup_manual_installments(enrollment, custom_data, counselor)

insts = list(enrollment.installments.order_by('installment_number'))
assert len(insts) == 3, f"Expected 3 installments, got {len(insts)}"
assert insts[0].scheduled_amount == Decimal('25000.00')
assert insts[1].scheduled_amount == Decimal('20000.00')
assert insts[2].scheduled_amount == Decimal('14000.00')
assert sum(i.scheduled_amount for i in insts) == enrollment.total_payable
print("✅ Test 1 Passed: _setup_manual_installments validated and created exact custom balanced installments.")

# 3. Test enrollment form rendering
factory = RequestFactory()
req = factory.get(f'/leads/{lead.id}/enroll/')
req.user = counselor
res = enrollment_create_or_edit(req, lead.id)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"

html = res.content.decode('utf-8')
assert "installment-calculator.js" in html, "Form must include installment-calculator.js script"
assert "Dynamic Installment Balancing Matrix" in html, "Form must render Dynamic Installment Balancing Matrix header"
assert "Equalize Remaining" in html, "Form must provide Equalize Remaining button"
assert "id_installment_method" in html, "Form must have id_installment_method hidden field"
print("✅ Test 2 Passed: Enrollment form rendered Dynamic Balancing Slider Matrix & Equalize tools with HTTP 200 OK.")

print("--- ALL TESTS PASSED FOR ITEM 146 ---")
