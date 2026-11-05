import os
import sys

sys.path.insert(0, r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from decimal import Decimal
from django.core.exceptions import ValidationError
from accounts.models import User, UserRole
from branches.models import Branch
from products.models import Product
from leads.models import Lead, Enrollment, PaymentTransaction, PaymentTransactionStatus
from leads.services_enrollment import record_payment, resubmit_payment

print("Starting UTR Shield Verification Test...")

branch, _ = Branch.objects.get_or_create(name="T. Nagar")
product, _ = Product.objects.get_or_create(name="Full Stack Python", defaults={'price': Decimal('35000.00')})
admin_user = User.objects.filter(role=UserRole.ADMIN).first()

lead1, _ = Lead.objects.get_or_create(name="Student Test 1", phone="9888811111", defaults={'branch': branch})
enrollment1, _ = Enrollment.objects.get_or_create(
    lead=lead1,
    defaults={
        'student_name': 'Student Test 1',
        'student_phone': '9888811111',
        'product': product,
        'branch': branch,
        'total_payable': Decimal('35000.00'),
        'outstanding_balance': Decimal('35000.00'),
        'enrollment_number': 'ENR-TEST-001'
    }
)

lead2, _ = Lead.objects.get_or_create(name="Student Test 2", phone="9888822222", defaults={'branch': branch})
enrollment2, _ = Enrollment.objects.get_or_create(
    lead=lead2,
    defaults={
        'student_name': 'Student Test 2',
        'student_phone': '9888822222',
        'product': product,
        'branch': branch,
        'total_payable': Decimal('35000.00'),
        'outstanding_balance': Decimal('35000.00'),
        'enrollment_number': 'ENR-TEST-002'
    }
)

test_utr = "UTR-TEST-UNIQUE-99901"

PaymentTransaction.objects.filter(transaction_reference=test_utr).delete()

# Test 1: Record payment for student 1 with test_utr -> Should SUCCEED
p1 = record_payment(
    enrollment1,
    admin_user,
    {
        'amount': Decimal('5000.00'),
        'payment_method': 'UPI',
        'transaction_reference': test_utr,
        'notes': 'Test payment 1',
        'auto_approve': True,
        'require_proof': False
    }
)
print(f"✅ Test 1 Passed: Payment 1 created successfully with Receipt #{p1.receipt_number}")

# Test 2: Record payment for student 2 with SAME test_utr -> Should FAIL with ValidationError
blocked = False
try:
    p2 = record_payment(
        enrollment2,
        admin_user,
        {
            'amount': Decimal('5000.00'),
            'payment_method': 'UPI',
            'transaction_reference': test_utr,
            'notes': 'Attempting duplicate UTR',
            'auto_approve': False,
            'require_proof': False
        }
    )
except ValidationError as e:
    blocked = True
    print(f"✅ Test 2 Passed: Duplicate UTR was blocked with error: {e}")

assert blocked, "Duplicate UTR was NOT blocked!"

# Test 3: Cash payments with empty reference should NOT trigger duplicate block
p_cash1 = record_payment(
    enrollment1,
    admin_user,
    {
        'amount': Decimal('1000.00'),
        'payment_method': 'Cash',
        'transaction_reference': '',
        'notes': 'Cash 1',
        'auto_approve': True,
        'require_proof': False
    }
)
p_cash2 = record_payment(
    enrollment2,
    admin_user,
    {
        'amount': Decimal('1000.00'),
        'payment_method': 'Cash',
        'transaction_reference': '',
        'notes': 'Cash 2',
        'auto_approve': True,
        'require_proof': False
    }
)
print(f"✅ Test 3 Passed: Cash payments without reference allowed cleanly ({p_cash1.receipt_number}, {p_cash2.receipt_number})")

# Clean up test transactions
PaymentTransaction.objects.filter(transaction_reference=test_utr).delete()
p_cash1.delete()
p_cash2.delete()

print("\n🎉 ALL UTR SHIELD TESTS PASSED PERFECTLY!")
