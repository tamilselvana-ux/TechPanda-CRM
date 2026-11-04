import os
import sys

sys.path.insert(0, r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test.utils import setup_test_environment
setup_test_environment()

from django.test import Client
from django.db import transaction
from decimal import Decimal
from accounts.models import User, UserRole
from branches.models import Branch
from products.models import Product
from leads.models import Lead
from leads.models_enrollment import Enrollment, PaymentPlan, PaymentTransaction, PaymentTransactionStatus

print("=== RUNNING TASK 2 (FIRST PAYMENT AT ENROLLMENT) VERIFICATION ===")

branch = Branch.objects.filter(status='Active').first()
if not branch:
    branch = Branch.objects.create(name="T2 Test Branch", status="Active")

counselor = User.objects.filter(role=UserRole.COUNSELOR, is_active=True).first()
if not counselor:
    counselor = User.objects.create_user(
        username="t2_counselor_run",
        email="counselor_t2_run@example.com",
        password="Password123!",
        role=UserRole.COUNSELOR,
        branch=branch
    )

product = Product.objects.filter(status=Product.Status.ACTIVE).first()
if not product:
    product = Product.objects.create(name="T2 Course", price=Decimal("35000.00"), status=Product.Status.ACTIVE)

client = Client()
client.force_login(counselor)

# TEST 1: Enrollment without first payment saves normally
with transaction.atomic():
    lead1 = Lead.objects.create(
        name="Student Normal",
        phone="9988112233",
        email="student_normal@example.com",
        branch=branch,
        product=product,
        assigned_counselor=counselor
    )
    post_data_1 = {
        'student_name': 'Student Normal',
        'student_phone': '9988112233',
        'student_email': 'student_normal@example.com',
        'product_id': product.id,
        'branch_id': branch.id,
        'base_course_fee': '35000.00',
        'gst_treatment': 'WITH_GST',
        'tax_rate': '18',
        'payment_plan': PaymentPlan.FULL_PAYMENT,
        'first_payment_amount': '',
    }
    res1 = client.post(f'/leads/{lead1.id}/enroll/', post_data_1)
    assert res1.status_code == 302, f"Expected 302 redirect, got {res1.status_code}"
    e1 = Enrollment.objects.filter(lead=lead1).first()
    assert e1 is not None, "Enrollment was not created"
    assert e1.payments.count() == 0, f"Expected 0 payments, got {e1.payments.count()}"
    print("PASS: Test 1 - Enrollment without first payment saves normally.")
    transaction.set_rollback(True)

# TEST 2: Enrollment with first payment saves atomically, creates payment in PENDING_VERIFICATION
with transaction.atomic():
    lead2 = Lead.objects.create(
        name="Student Initial Pay",
        phone="9988112244",
        email="student_pay@example.com",
        branch=branch,
        product=product,
        assigned_counselor=counselor
    )
    post_data_2 = {
        'student_name': 'Student Initial Pay',
        'student_phone': '9988112244',
        'student_email': 'student_pay@example.com',
        'product_id': product.id,
        'branch_id': branch.id,
        'base_course_fee': '35000.00',
        'gst_treatment': 'WITHOUT_GST',
        'payment_plan': PaymentPlan.FULL_PAYMENT,
        'first_payment_amount': '15000.00',
        'first_payment_method': 'UPI',
        'first_payment_reference': 'UPI-TEST-12345',
        'first_payment_notes': 'Initial token payment at registration',
    }
    res2 = client.post(f'/leads/{lead2.id}/enroll/', post_data_2)
    assert res2.status_code == 302, f"Expected 302 redirect, got {res2.status_code}"
    e2 = Enrollment.objects.filter(lead=lead2).first()
    assert e2 is not None, "Enrollment was not created"
    assert e2.payments.count() == 1, f"Expected 1 payment, got {e2.payments.count()}"
    p2 = e2.payments.first()
    assert p2.amount == Decimal('15000.00'), f"Expected amount 15000.00, got {p2.amount}"
    assert p2.status == PaymentTransactionStatus.PENDING_VERIFICATION, f"Expected PENDING_VERIFICATION, got {p2.status}"
    assert p2.payment_method == 'UPI', f"Expected UPI, got {p2.payment_method}"
    assert p2.transaction_reference == 'UPI-TEST-12345'
    assert p2.recorded_by == counselor
    print("PASS: Test 2 - Enrollment with initial payment created atomically in PENDING_VERIFICATION.")
    transaction.set_rollback(True)

# TEST 3: Validation failure (Amount exceeds course fee) rolls back entire enrollment
with transaction.atomic():
    lead3 = Lead.objects.create(
        name="Student Invalid Amount",
        phone="9988112255",
        email="student_invalid@example.com",
        branch=branch,
        product=product,
        assigned_counselor=counselor
    )
    post_data_3 = {
        'student_name': 'Student Invalid Amount',
        'student_phone': '9988112255',
        'student_email': 'student_invalid@example.com',
        'product_id': product.id,
        'branch_id': branch.id,
        'base_course_fee': '35000.00',
        'gst_treatment': 'WITHOUT_GST',
        'payment_plan': PaymentPlan.FULL_PAYMENT,
        'first_payment_amount': '99999.00', # Exceeds fee!
        'first_payment_method': 'Cash',
    }
    res3 = client.post(f'/leads/{lead3.id}/enroll/', post_data_3)
    assert res3.status_code == 200, f"Expected re-rendered form with status 200, got {res3.status_code}"
    e3 = Enrollment.objects.filter(lead=lead3).first()
    assert e3 is None, "Enrollment MUST be rolled back if first payment validation fails!"
    print("PASS: Test 3 - Excess payment amount rolls back enrollment atomically.")
    transaction.set_rollback(True)

# TEST 4: Validation failure (Missing reference number for UPI) rolls back entire enrollment
with transaction.atomic():
    lead4 = Lead.objects.create(
        name="Student Missing Ref",
        phone="9988112266",
        email="student_noref@example.com",
        branch=branch,
        product=product,
        assigned_counselor=counselor
    )
    post_data_4 = {
        'student_name': 'Student Missing Ref',
        'student_phone': '9988112266',
        'student_email': 'student_noref@example.com',
        'product_id': product.id,
        'branch_id': branch.id,
        'base_course_fee': '35000.00',
        'gst_treatment': 'WITHOUT_GST',
        'payment_plan': PaymentPlan.FULL_PAYMENT,
        'first_payment_amount': '5000.00',
        'first_payment_method': 'UPI',
        'first_payment_reference': '', # Missing ref!
    }
    res4 = client.post(f'/leads/{lead4.id}/enroll/', post_data_4)
    assert res4.status_code == 200, f"Expected 200, got {res4.status_code}"
    e4 = Enrollment.objects.filter(lead=lead4).first()
    assert e4 is None, "Enrollment MUST be rolled back if required reference is missing!"
    print("PASS: Test 4 - Missing reference for online mode rolls back enrollment atomically.")
    transaction.set_rollback(True)

print("\nALL TASK 2 TESTS PASSED PERFECTLY!")
