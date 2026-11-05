import os
import sys

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import RequestFactory
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from leads.models import Lead
from branches.models import Branch
from products.models import Product
from leads.models_enrollment import Enrollment, Installment, InstallmentStatus, PaymentEmailLog
from chat.models import Conversation, Message, BusinessAccount
from finance.dunning import run_dunning_cycle
from finance.views import finance_dunning_trigger
from accounts.models import UserRole
import json

User = get_user_model()

print("--- TESTING ITEM 148: AUTOMATED OVERDUE INSTALLMENT DUNNING ENGINE ---")

# 1. Setup Admin & Test Branch
admin, _ = User.objects.get_or_create(
    username="admin_dunning_test",
    defaults={"role": UserRole.ADMIN, "first_name": "Admin", "last_name": "User"}
)
admin.role = UserRole.ADMIN
admin.save()

branch, _ = Branch.objects.get_or_create(name="Dunning Center", defaults={"address": "Dunning Road", "phone": "044-33221100"})
product, _ = Product.objects.get_or_create(name="AI Cloud Architect", defaults={"price": 75000})

biz, _ = BusinessAccount.objects.get_or_create(
    phone_number_id="55443322",
    defaults={"name": "iTechPanda Official", "phone_number": "+919988776655"}
)

today = timezone.localdate()

# 2. Setup 3 Leads + Enrollments + Installments
# Case A: Due in 3 days (Stage 1)
lead_a, _ = Lead.objects.get_or_create(
    phone="9840111111",
    defaults={"name": "Student Stage1", "email": "s1@example.com", "branch": branch, "product": product}
)
conv_a, _ = Conversation.objects.get_or_create(
    phone_number="+919840111111",
    defaults={"customer_name": lead_a.name, "business_account": biz}
)
enr_a, _ = Enrollment.objects.get_or_create(
    lead=lead_a,
    defaults={"enrollment_number": "ENR-DUN-001", "student_name": lead_a.name, "student_phone": lead_a.phone, "student_email": lead_a.email, "product": product, "total_payable": 75000, "status": "Active"}
)
inst_a, _ = Installment.objects.get_or_create(
    enrollment=enr_a,
    installment_number=1,
    defaults={"scheduled_amount": 25000, "remaining_balance": 25000, "due_date": today + timedelta(days=3), "status": InstallmentStatus.UPCOMING}
)
inst_a.due_date = today + timedelta(days=3)
inst_a.remaining_balance = Decimal('25000.00')
inst_a.save()

# Case B: Due Today (Stage 2)
lead_b, _ = Lead.objects.get_or_create(
    phone="9840222222",
    defaults={"name": "Student Stage2", "email": "s2@example.com", "branch": branch, "product": product}
)
conv_b, _ = Conversation.objects.get_or_create(
    phone_number="+919840222222",
    defaults={"customer_name": lead_b.name, "business_account": biz}
)
enr_b, _ = Enrollment.objects.get_or_create(
    lead=lead_b,
    defaults={"enrollment_number": "ENR-DUN-002", "student_name": lead_b.name, "student_phone": lead_b.phone, "student_email": lead_b.email, "product": product, "total_payable": 75000, "status": "Active"}
)
inst_b, _ = Installment.objects.get_or_create(
    enrollment=enr_b,
    installment_number=1,
    defaults={"scheduled_amount": 25000, "remaining_balance": 25000, "due_date": today, "status": InstallmentStatus.DUE}
)
inst_b.due_date = today
inst_b.remaining_balance = Decimal('25000.00')
inst_b.save()

# Case C: Overdue by 6 days (Stage 3)
lead_c, _ = Lead.objects.get_or_create(
    phone="9840333333",
    defaults={"name": "Student Stage3", "email": "s3@example.com", "branch": branch, "product": product}
)
conv_c, _ = Conversation.objects.get_or_create(
    phone_number="+919840333333",
    defaults={"customer_name": lead_c.name, "business_account": biz}
)
enr_c, _ = Enrollment.objects.get_or_create(
    lead=lead_c,
    defaults={"enrollment_number": "ENR-DUN-003", "student_name": lead_c.name, "student_phone": lead_c.phone, "student_email": lead_c.email, "product": product, "total_payable": 75000, "status": "Active"}
)
inst_c, _ = Installment.objects.get_or_create(
    enrollment=enr_c,
    installment_number=1,
    defaults={"scheduled_amount": 25000, "remaining_balance": 25000, "due_date": today - timedelta(days=6), "status": InstallmentStatus.UPCOMING}
)
inst_c.due_date = today - timedelta(days=6)
inst_c.remaining_balance = Decimal('25000.00')
inst_c.save()

# Clean up any existing logs from today for these installments
PaymentEmailLog.objects.filter(installment__in=[inst_a, inst_b, inst_c]).delete()

# 3. Execute Dunning Cycle
summary = run_dunning_cycle(target_date=today)
assert summary['stage_1_upcoming'] >= 1, f"Expected at least 1 Stage 1, got {summary['stage_1_upcoming']}"
assert summary['stage_2_due'] >= 1, f"Expected at least 1 Stage 2, got {summary['stage_2_due']}"
assert summary['stage_3_overdue'] >= 1, f"Expected at least 1 Stage 3, got {summary['stage_3_overdue']}"
assert summary['total_dispatched'] >= 3

# Verify Stage 3 set status to OVERDUE
inst_c.refresh_from_db()
assert inst_c.status == InstallmentStatus.OVERDUE, f"Expected Overdue, got {inst_c.status}"

# Verify PaymentEmailLog entries created
logs = PaymentEmailLog.objects.filter(installment__in=[inst_a, inst_b, inst_c])
assert logs.count() == 3, f"Expected 3 logs, got {logs.count()}"
print("✅ Test 1 Passed: Dunning engine processed Stage 1 (T-3), Stage 2 (Due Today), and Stage 3 (T+5 Overdue Escalation).")

# 4. Test Idempotency: Second run should process 0 duplicates
summary_idempotent = run_dunning_cycle(target_date=today)
assert summary_idempotent['stage_1_upcoming'] == 0
assert summary_idempotent['stage_2_due'] == 0
assert summary_idempotent['stage_3_overdue'] == 0
assert summary_idempotent['total_dispatched'] == 0
print("✅ Test 2 Passed: Dunning engine is 100% idempotent; second run dispatched 0 duplicate reminders.")

# 5. Test Trigger Endpoint
factory = RequestFactory()
req = factory.post('/finance/dunning/trigger/')
req.user = admin
res = finance_dunning_trigger(req)
assert res.status_code == 200
data = json.loads(res.content.decode('utf-8'))
assert data['success'] is True
assert 'summary' in data
print("✅ Test 3 Passed: /finance/dunning/trigger/ endpoint returned HTTP 200 with valid execution summary.")

print("--- ALL TESTS PASSED FOR ITEM 148 ---")
