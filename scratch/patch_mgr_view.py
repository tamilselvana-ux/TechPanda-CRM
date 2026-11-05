import os

views_path = 'leads/views.py' if os.path.exists('leads/views.py') else 'CRM/leads/views.py'
with open(views_path, 'r', encoding='utf-8') as f:
    content = f.read()

# In manager_leads_list:
target_var = "    product_filter = request.GET.get('product', '').strip()\n\n    branch_filter = request.GET.get('branch', '').strip()"
replacement_var = "    product_filter = request.GET.get('product', '').strip()\n\n    branch_filter = request.GET.get('branch', '').strip()\n\n    sla_filter = request.GET.get('sla', '').strip()"

if target_var in content:
    content = content.replace(target_var, replacement_var, 1)
    print("Added sla_filter var to manager_leads_list")
else:
    print("target_var not found")

target_filter = """    if product_filter:

        leads_qs = leads_qs.filter(product_id=product_filter)"""

replacement_filter = """    if product_filter:

        leads_qs = leads_qs.filter(product_id=product_filter)

    if sla_filter:
        now = timezone.now()
        if sla_filter == 'breached':
            two_hours_ago = now - timedelta(hours=2)
            leads_qs = leads_qs.filter(status='New', created_at__lte=two_hours_ago)
        elif sla_filter == 'warning':
            two_hours_ago = now - timedelta(hours=2)
            thirty_mins_ago = now - timedelta(minutes=30)
            leads_qs = leads_qs.filter(status='New', created_at__gte=two_hours_ago, created_at__lte=thirty_mins_ago)
        elif sla_filter == 'fresh':
            thirty_mins_ago = now - timedelta(minutes=30)
            leads_qs = leads_qs.filter(status='New', created_at__gt=thirty_mins_ago)"""

if target_filter in content:
    content = content.replace(target_filter, replacement_filter, 1)
    print("Added sla_filter queryset logic to manager_leads_list")
else:
    print("target_filter not found")

target_ctx = "        'product_filter': product_filter,\n        'branch_filter': branch_filter,"
replacement_ctx = "        'product_filter': product_filter,\n        'sla_filter': sla_filter,\n        'branch_filter': branch_filter,"

if target_ctx in content:
    content = content.replace(target_ctx, replacement_ctx, 1)
    print("Added sla_filter to manager_leads_list context")
else:
    print("target_ctx not found")

with open(views_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("MANAGER_PATCH_FINISHED")
