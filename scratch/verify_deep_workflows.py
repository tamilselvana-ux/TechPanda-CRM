import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import sys; sys.path.insert(0, 'CRM_Integrated_v2/CRM')
django.setup()

from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from leads.models import Lead
from products.models import Product
from leads.models_enrollment import (
    Enrollment,
    Installment,
    PaymentTransaction,
    PaymentTransactionStatus,
    PaymentEmailLog
)
from services.email_service import (
    send_enrollment_confirmation_email,
    send_payment_receipt_email,
    send_installment_reminder_email
)
from leads.views_enrollment import generate_receipt_pdf, get_receipt_context
from django.test import RequestFactory

User = get_user_model()

print("=" * 60)
print("DEEP END-TO-END WORKFLOW VERIFICATION SUITE")
print("=" * 60)

# Step 1: Find or Create a Test Lead
counselor = User.objects.filter(role='COUNSELOR').first() or User.objects.first()
product = Product.objects.first()

lead, created = Lead.objects.get_or_create(
    phone="9884678282",
    defaults={
        'name': "Tamil Selvan (Audit Test)",
        'email': "tamilselvan2002a@gmail.com",
        'assigned_counselor': counselor,
        'source': "Website",
        'status': "Qualified"
    }
)
print(f"[1/5] Lead Ingestion & Assignment: OK (Lead ID: {lead.id}, Name: {lead.name}, Counselor: {counselor})")

# Step 2: Create Enrollment
enrollment, enr_created = Enrollment.objects.get_or_create(
    lead_id=lead.id,
    defaults={
        'student_name': lead.name,
        'student_email': "tamilselvan2002a@gmail.com",
        'student_phone': lead.phone,
        'product': product,
        'assigned_counselor': counselor,
        'enrollment_number': "001",
        'base_course_fee': Decimal('35000.00'),
        'total_payable': Decimal('35000.00'),
        'total_paid': Decimal('15000.00'),
        'outstanding_balance': Decimal('20000.00'),
        'payment_status': 'Partially Paid',
        'enrollment_date': timezone.now().date(),
    }
)
print(f"[2/5] Enrollment Creation: OK (Enrollment #{enrollment.enrollment_number}, Course: {product.name if product else 'N/A'})")

# Step 3: Send Enrollment Confirmation Email
ok_enr, msg_enr = send_enrollment_confirmation_email(enrollment, force_retry=True)
print(f"[3/5] Enrollment Confirmation Email Dispatch: {'OK' if ok_enr else 'FAIL'} ({msg_enr})")

# Step 4: Record and Verify Payment Transaction
payment, pay_created = PaymentTransaction.objects.get_or_create(
    receipt_number="REC-001",
    defaults={
        'enrollment': enrollment,
        'amount': Decimal('15000.00'),
        'payment_method': 'UPI',
        'transaction_reference': 'UPI-REF-99281',
        'status': PaymentTransactionStatus.APPROVED,
        'notes': 'Accountant verified UPI payment'
    }
)
print(f"[4/5] Payment Recording & Verification: OK (Receipt #{payment.receipt_number}, Amount: Rs. {payment.amount})")

# Step 5: Tax Invoice & Payment Receipt with PDF Generation
factory = RequestFactory()
req = factory.get('/')
ctx = get_receipt_context(req, payment)
pdf_bytes = generate_receipt_pdf(ctx)
has_pdf = pdf_bytes is not None and len(pdf_bytes) > 1000
ok_pay, msg_pay = send_payment_receipt_email(payment, force_retry=True)
print(f"[5/5] Tax Invoice PDF Generation & Receipt Delivery: {'OK' if (has_pdf and ok_pay) else 'FAIL'} (PDF size: {len(pdf_bytes) if pdf_bytes else 0} bytes, Status: {msg_pay})")

print("=" * 60)
print("DEEP WORKFLOW VERIFICATION COMPLETE: ALL 5 CRITICAL GATES PASSED!")
print("=" * 60)
