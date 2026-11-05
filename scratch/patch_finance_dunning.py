import os

# 1. Update finance/views.py
views_path = 'finance/views.py' if os.path.exists('finance/views.py') else 'CRM/finance/views.py'
with open(views_path, 'r', encoding='utf-8') as f:
    views_code = f.read()

view_func = '''
@login_required
def finance_dunning_trigger(request):
    """
    Triggers automated overdue installment dunning cycle on demand.
    Available to Admin, Finance Head, and Sales Head roles.
    """
    if not (request.user.is_admin_user or request.user.role in (UserRole.SALES_HEAD, UserRole.FINANCE_HEAD)):
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

    from .dunning import run_dunning_cycle
    summary = run_dunning_cycle()
    return JsonResponse({'success': True, 'summary': summary})
'''

if "def finance_dunning_trigger" not in views_code:
    views_code += "\n" + view_func
    with open(views_path, 'w', encoding='utf-8') as f:
        f.write(views_code)
    print("ADDED_FINANCE_DUNNING_TRIGGER_VIEW")
else:
    print("VIEW_ALREADY_PRESENT")

# 2. Update finance/urls.py
urls_path = 'finance/urls.py' if os.path.exists('finance/urls.py') else 'CRM/finance/urls.py'
with open(urls_path, 'r', encoding='utf-8') as f:
    urls_code = f.read()

route = "    # Dunning Engine\n    path('dunning/trigger/', views.finance_dunning_trigger, name='finance_dunning_trigger'),\n]"
idx = urls_code.rfind(']')
if idx != -1 and "finance_dunning_trigger" not in urls_code:
    urls_code = urls_code[:idx] + route + urls_code[idx+1:]
    with open(urls_path, 'w', encoding='utf-8') as f:
        f.write(urls_code)
    print("ADDED_FINANCE_DUNNING_ROUTE")
else:
    print("ROUTE_ALREADY_PRESENT_OR_NOT_FOUND")
