import os

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\views_accountant.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    branches = Branch.objects.filter(id__in=get_accessible_branch_ids(request.user), status='Active')"""

replacement = """    page_refs = [p.transaction_reference.strip() for p in page_obj if p.transaction_reference and p.transaction_reference.strip() and p.payment_method != PaymentMethod.CASH]
    duplicate_refs = set()
    if page_refs:
        from django.db.models import Count
        duplicate_refs = set(
            PaymentTransaction.objects.filter(
                transaction_reference__in=page_refs
            ).exclude(
                status=PaymentTransactionStatus.REJECTED
            ).values('transaction_reference')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)
            .values_list('transaction_reference', flat=True)
        )

    branches = Branch.objects.filter(id__in=get_accessible_branch_ids(request.user), status='Active')"""

target_ctx = """        'rejected_count': rejected_count,
        'portal_title': 'Payment Verification Queue',"""

replacement_ctx = """        'rejected_count': rejected_count,
        'duplicate_refs': duplicate_refs,
        'portal_title': 'Payment Verification Queue',"""

if target in content:
    content = content.replace(target, replacement, 1)
    print("Replaced target in views_accountant.py")
else:
    print("Warning: target not found in views_accountant.py")

if target_ctx in content:
    content = content.replace(target_ctx, replacement_ctx, 1)
    print("Replaced target_ctx in views_accountant.py")
else:
    print("Warning: target_ctx not found in views_accountant.py")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Finished patching views_accountant.py")
