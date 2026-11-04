import os, sys, subprocess, json
from pathlib import Path

sys.path.insert(0, os.path.abspath('CRM_Integrated_v2/CRM'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.conf import settings

User = get_user_model()
admin = User.objects.filter(is_superuser=True).first() or User.objects.filter(role='admin').first()

session = SessionStore()
session['_auth_user_id'] = str(admin.pk)
session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
session['_auth_user_hash'] = admin.get_session_auth_hash()
session.save()
session_key = session.session_key
print(f"Generated session key: {session_key} for admin: {admin.username}")

# Save cookie script for Chrome via CDP or devtools
# In Chrome headless, we can load a small HTML runner or pass cookies
out_dir = Path('docs/qa/calendar_baseline')
out_dir.mkdir(parents=True, exist_ok=True)
print(f"Baseline directory ready: {out_dir}")
