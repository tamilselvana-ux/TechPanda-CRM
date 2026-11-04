import re

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\views_enrollment.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add from django.db import transaction if missing
if 'from django.db import transaction' not in content:
    content = content.replace('from django.db.models import Sum, Q, Count', 'from django.db import transaction\nfrom django.db.models import Sum, Q, Count', 1)

# 2. Replace try/create_or_update_enrollment in enrollment_create_or_edit
old_block = """        try:

            saved_enrollment = create_or_update_enrollment(lead, request.user, data)

            messages.success(request, f"Enrollment #{saved_enrollment.enrollment_number} successfully registered for {saved_enrollment.student_name}.")

            return redirect('counselor_enrolled_students' if request.user.role == UserRole.COUNSELOR else 'admin_enrolled_students')

        except (ValidationError, PermissionDenied, Exception) as exc:

            messages.error(request, f"Enrollment failed: {exc}")"""

new_block = """        try:
            with transaction.atomic():
                saved_enrollment = create_or_update_enrollment(lead, request.user, data)

                # Optional First Payment at enrollment
                raw_first_amt = (request.POST.get('first_payment_amount') or '').strip()
                first_txn = None
                if raw_first_amt:
                    try:
                        first_amt = Decimal(raw_first_amt).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    except Exception:
                        raise ValidationError("Invalid first payment amount.")

                    if first_amt <= Decimal('0.00'):
                        raise ValidationError("First payment amount must be greater than zero.")

                    if first_amt > saved_enrollment.total_course_fee:
                        raise ValidationError(f"First payment amount (₹{first_amt:,.2f}) cannot exceed the total course fee (₹{saved_enrollment.total_course_fee:,.2f}).")

                    payment_method = request.POST.get('first_payment_method', PaymentMethod.UPI)
                    ref_no = (request.POST.get('first_payment_reference') or '').strip()

                    # Transaction / reference number is required for UPI, Card, Bank Transfer and Cheque
                    if payment_method in [PaymentMethod.UPI, PaymentMethod.CARD, PaymentMethod.BANK_TRANSFER, PaymentMethod.CHEQUE]:
                        if not ref_no:
                            raise ValidationError(f"Transaction / Reference number is required for payment mode '{payment_method}'.")

                    first_date_raw = (request.POST.get('first_payment_date') or '').strip()
                    try:
                        payment_date = timezone.datetime.strptime(first_date_raw, '%Y-%m-%d').date() if first_date_raw else timezone.localdate()
                    except (ValueError, TypeError):
                        payment_date = timezone.localdate()

                    payment_proof = request.FILES.get('first_payment_proof')
                    notes = (request.POST.get('first_payment_notes') or '').strip()

                    first_txn = record_payment(
                        enrollment=saved_enrollment,
                        amount_or_user=request.user,
                        payment_method_or_data={
                            'amount': first_amt,
                            'payment_method': payment_method,
                            'transaction_reference': ref_no,
                            'notes': notes,
                            'payment_proof': payment_proof,
                            'auto_approve': False,  # Queued for Accountant verification
                            'require_proof': False, # Optional proof upload on enrollment
                        }
                    )
                    if payment_date != timezone.localdate():
                        from datetime import datetime, time
                        first_txn.payment_date = timezone.make_aware(datetime.combine(payment_date, time.min))
                        first_txn.save(update_fields=['payment_date'])

            messages.success(request, f"Enrollment #{saved_enrollment.enrollment_number} successfully registered for {saved_enrollment.student_name}.")
            if first_txn:
                messages.info(request, f"Initial payment of ₹{first_txn.amount:,.2f} recorded (#{first_txn.receipt_number}) and sent to Accountant for verification.")
            return redirect('counselor_enrolled_students' if request.user.role == UserRole.COUNSELOR else 'admin_enrolled_students')

        except (ValidationError, PermissionDenied, Exception) as exc:
            messages.error(request, f"Enrollment failed: {exc}")"""

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    print("Replaced enrollment save block with atomic first-payment logic!")
else:
    # Try regex fallback for flexible newlines
    pattern = re.compile(r'try:\s+saved_enrollment = create_or_update_enrollment\(lead, request\.user, data\)\s+messages\.success\(request, f"Enrollment #\{saved_enrollment\.enrollment_number\} successfully registered for \{saved_enrollment\.student_name\}\."\)\s+return redirect\(\'counselor_enrolled_students\' if request\.user\.role == UserRole\.COUNSELOR else \'admin_enrolled_students\'\)\s+except \(ValidationError, PermissionDenied, Exception\) as exc:\s+messages\.error\(request, f"Enrollment failed: \{exc\}"\)')
    if pattern.search(content):
        content = pattern.sub(new_block, content, count=1)
        print("Replaced via regex pattern!")
    else:
        print("ERROR: old_block not found!")

# 3. Add context for GET
old_ctx = """        'default_gst_rate': Enrollment.get_default_gst_rate(),

    })"""
new_ctx = """        'default_gst_rate': Enrollment.get_default_gst_rate(),
        'today_str': timezone.localdate().strftime('%Y-%m-%d'),
        'payment_methods': PaymentMethod.choices,
    })"""
if old_ctx in content:
    content = content.replace(old_ctx, new_ctx, 1)
    print("Added today_str and payment_methods to GET context!")
else:
    print("Warning: old_ctx not found directly, checking regex...")
    pattern_ctx = re.compile(r"\'default_gst_rate\': Enrollment\.get_default_gst_rate\(\),\s+\}\)")
    content = pattern_ctx.sub(r"'default_gst_rate': Enrollment.get_default_gst_rate(),\n        'today_str': timezone.localdate().strftime('%Y-%m-%d'),\n        'payment_methods': PaymentMethod.choices,\n    })", content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Finished patching views_enrollment.py")
