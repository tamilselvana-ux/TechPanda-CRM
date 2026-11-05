import os

path = 'leads/urls.py' if os.path.exists('leads/urls.py') else 'CRM/leads/urls.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import
if 'views_360' not in content:
    content = content.replace('views_email_logs', 'views_email_logs, views_360', 1)

# 2. Add route before ]
if 'lead_360_data' not in content:
    route = "    # Student 360° Unified Admissions Drawer\n    path('leads/<int:lead_id>/360-data/', views_360.lead_360_data, name='lead_360_data'),\n]"
    idx = content.rfind(']')
    if idx != -1:
        content = content[:idx] + route + content[idx+1:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("URLS_PATCHED")
