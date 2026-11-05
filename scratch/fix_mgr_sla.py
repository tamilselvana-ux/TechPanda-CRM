import os, re

path = 'leads/views.py' if os.path.exists('leads/views.py') else 'CRM/leads/views.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r"(def manager_leads_list\(request\):[\s\S]*?leads_qs\s*=\s*leads_qs\.filter\(product_id=product_filter\))([\s\S]*?)(leads_qs\s*=\s*leads_qs\.order_by\('-created_at')"

def repl(m):
    block = """\n\n    if sla_filter:\n        now = timezone.now()\n        if sla_filter == 'breached':\n            two_hours_ago = now - timedelta(hours=2)\n            leads_qs = leads_qs.filter(status='New', created_at__lte=two_hours_ago)\n        elif sla_filter == 'warning':\n            two_hours_ago = now - timedelta(hours=2)\n            thirty_mins_ago = now - timedelta(minutes=30)\n            leads_qs = leads_qs.filter(status='New', created_at__gte=two_hours_ago, created_at__lte=thirty_mins_ago)\n        elif sla_filter == 'fresh':\n            thirty_mins_ago = now - timedelta(minutes=30)\n            leads_qs = leads_qs.filter(status='New', created_at__gt=thirty_mins_ago)\n\n    """
    return m.group(1) + block + m.group(3)

new_text, count = re.subn(pattern, repl, text, count=1)
if count > 0:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("SUCCESSFULLY_PATCHED_MANAGER_LEADS_SLA_QUERY")
else:
    print("FAILED_TO_MATCH_PATTERN")
