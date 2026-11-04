import os, sys, json, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, 'CRM_Integrated_v2/CRM')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import Client

User = get_user_model()

sessions = {}

# 1. Superadmin (hi)
u_admin = User.objects.filter(is_superuser=True).first()
if u_admin:
    c = Client()
    c.force_login(u_admin)
    sessions['admin'] = c.cookies['sessionid'].value
    print(f"Admin ({u_admin.username}) session: {sessions['admin']}")

# 2. Counselor
u_counselor = User.objects.filter(role='COUNSELOR').first()
if u_counselor:
    c = Client()
    c.force_login(u_counselor)
    sessions['counselor'] = c.cookies['sessionid'].value
    print(f"Counselor ({u_counselor.username}) session: {sessions['counselor']}")

# 3. Telecaller
u_telecaller = User.objects.filter(role='TELECALLER').first()
if u_telecaller:
    c = Client()
    c.force_login(u_telecaller)
    sessions['telecaller'] = c.cookies['sessionid'].value
    print(f"Telecaller ({u_telecaller.username}) session: {sessions['telecaller']}")

with open('CRM_Integrated_v2/CRM/scratch/sessions.json', 'w') as f:
    json.dump(sessions, f)

print("Saved sessions to scratch/sessions.json")
