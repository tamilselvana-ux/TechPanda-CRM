import os, sys, json, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, 'CRM_Integrated_v2/CRM')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

roles_map = {
    'admin': User.objects.filter(role='SUPERADMIN', is_active=True).first(),
    'accountant': User.objects.filter(role='ACCOUNTANT', is_active=True).first(),
    'counselor': User.objects.filter(role='COUNSELOR', is_active=True).first(),
    'telecaller': User.objects.filter(role='TELECALLER', is_active=True).first(),
    'branch_head': User.objects.filter(role='BRANCH_HEAD', is_active=True).first(),
    'sales_head': User.objects.filter(role='SALES_HEAD', is_active=True).first(),
    'receptionist': User.objects.filter(role='RECEPTIONIST', is_active=True).first(),
}

sessions = {}
for role_name, user in roles_map.items():
    if user:
        c = Client()
        c.force_login(user)
        sessions[role_name] = {
            'username': user.username,
            'role': user.role,
            'sessionid': c.cookies['sessionid'].value
        }
        print(f"Generated session for {role_name} ({user.username}): {c.cookies['sessionid'].value}")
    else:
        print(f"WARNING: No active user for {role_name}")

os.makedirs('docs', exist_ok=True)
with open('docs/role_sessions.json', 'w') as f:
    json.dump(sessions, f, indent=2)

print("Saved all role sessions to docs/role_sessions.json")
