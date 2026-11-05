import os

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\services_enrollment.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    if payment_proof:
        validate_payment_proof(payment_proof)

    # Generate unique receipt number"""

replacement = """    if payment_proof:
        validate_payment_proof(payment_proof)

    # Financial Duplicate UTR Shield: Prevent duplicate transaction reference entries across active payments
    clean_ref = str(transaction_reference or '').strip()
    if clean_ref and payment_method != PaymentMethod.CASH:
        existing_dup = PaymentTransaction.objects.filter(
            transaction_reference__iexact=clean_ref
        ).exclude(
            status=PaymentTransactionStatus.REJECTED
        ).select_related('enrollment').first()
        if existing_dup:
            st_name = existing_dup.enrollment.student_name if existing_dup.enrollment else 'Another student'
            dt_str = existing_dup.payment_date.strftime('%d-%b-%Y') if existing_dup.payment_date else 'earlier'
            raise ValidationError(
                f"Duplicate Transaction Reference! UTR / Ref '{clean_ref}' was already recorded for student '{st_name}' on {dt_str} (Receipt #{existing_dup.receipt_number}, Status: {existing_dup.status}). Please enter a unique transaction reference."
            )

    # Generate unique receipt number"""

if target in content:
    content = content.replace(target, replacement, 1)
    print("Replaced target 1")
else:
    print("Warning: target 1 not found")

target2 = """    if 'transaction_reference' in data:
        payment.transaction_reference = str(data['transaction_reference']).strip()
        update_fields.append('transaction_reference')"""

replacement2 = """    if 'transaction_reference' in data:
        new_ref = str(data['transaction_reference']).strip()
        if new_ref and payment.payment_method != PaymentMethod.CASH:
            existing_dup = PaymentTransaction.objects.filter(
                transaction_reference__iexact=new_ref
            ).exclude(
                id=payment.id
            ).exclude(
                status=PaymentTransactionStatus.REJECTED
            ).select_related('enrollment').first()
            if existing_dup:
                st_name = existing_dup.enrollment.student_name if existing_dup.enrollment else 'Another student'
                dt_str = existing_dup.payment_date.strftime('%d-%b-%Y') if existing_dup.payment_date else 'earlier'
                raise ValidationError(
                    f"Duplicate Transaction Reference! UTR / Ref '{new_ref}' was already recorded for student '{st_name}' on {dt_str} (Receipt #{existing_dup.receipt_number}, Status: {existing_dup.status})."
                )
        payment.transaction_reference = new_ref
        update_fields.append('transaction_reference')"""

if target2 in content:
    content = content.replace(target2, replacement2, 1)
    print("Replaced target 2")
else:
    print("Warning: target 2 not found")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Finished patching services_enrollment.py")
