import os

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\views_accountant.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Clean up from accountant_dashboard (where page_obj didn't exist)
bad_snippet = """    page_refs = [p.transaction_reference.strip() for p in page_obj if p.transaction_reference and p.transaction_reference.strip() and p.payment_method != PaymentMethod.CASH]
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
        )"""

content = content.replace(bad_snippet + "\n\n", "")

# 2. Add into accountant_payment_verification right after paginator page_obj is defined
target = """    branches = Branch.objects.filter(id__in=get_accessible_branch_ids(request.user), status='Active')
    counselors = User.objects.filter(
        role=UserRole.COUNSELOR,
        branch_id__in=branch_ids,
        is_active=True
    ).order_by('first_name')"""

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

    branches = Branch.objects.filter(id__in=get_accessible_branch_ids(request.user), status='Active')
    counselors = User.objects.filter(
        role=UserRole.COUNSELOR,
        branch_id__in=branch_ids,
        is_active=True
    ).order_by('first_name')"""

content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed duplicate_refs placement in views_accountant.py")
