import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import sys; sys.path.insert(0, 'CRM_Integrated_v2/CRM')
django.setup()

from services.email_service import (
    send_enrollment_confirmation_email,
    send_payment_receipt_email,
    send_installment_reminder_email
)
from leads.models_enrollment import Enrollment, PaymentTransaction, Installment

TARGET_EMAIL = 'tamilselvan2002a@gmail.com'

print(f"Sending sample emails to {TARGET_EMAIL}...")

# 1. Enrollment confirmation
e = Enrollment.objects.first()
if e:
    orig = e.student_email
    e.student_email = TARGET_EMAIL
    e.save(update_fields=['student_email'])
    ok1, msg1 = send_enrollment_confirmation_email(e, force_retry=True)
    print("1. Enrollment Confirmation:", ok1, msg1)
    e.student_email = orig
    e.save(update_fields=['student_email'])

# 2. Payment receipt & Tax invoice
p = PaymentTransaction.objects.filter(status='SUCCESS').first() or PaymentTransaction.objects.first()
if p and p.enrollment:
    orig = p.enrollment.student_email
    p.enrollment.student_email = TARGET_EMAIL
    p.enrollment.save(update_fields=['student_email'])
    ok2, msg2 = send_payment_receipt_email(p, force_retry=True)
    print("2. Payment Receipt & Tax Invoice:", ok2, msg2)
    p.enrollment.student_email = orig
    p.enrollment.save(update_fields=['student_email'])

# 3. Installment reminder
inst = Installment.objects.filter(status='PENDING').first() or Installment.objects.first()
if inst and inst.enrollment:
    orig = inst.enrollment.student_email
    inst.enrollment.student_email = TARGET_EMAIL
    inst.enrollment.save(update_fields=['student_email'])
    ok3, msg3 = send_installment_reminder_email(inst, reminder_type='DUE_REMINDER', force_retry=True)
    print("3. Installment Reminder:", ok3, msg3)
    inst.enrollment.student_email = orig
    inst.enrollment.save(update_fields=['student_email'])
