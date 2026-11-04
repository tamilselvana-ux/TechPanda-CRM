import sys, os
sys.path.insert(0, r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django; django.setup()
from django.test import Client
from accounts.models import User, UserRole

admin = User.objects.filter(role=UserRole.ADMIN, is_active=True).first()
c = Client()
c.force_login(admin)
r = c.get("/admin/dashboard/")
html = r.content.decode("utf-8")

import re
print("Has form.filter-form select:", bool(re.search(r'<form[^>]*class="[^"]*filter-form[^"]*"[^>]*>.*?<select', html, re.DOTALL)))
print("Has .filter-card select:", bool(re.search(r'class="[^"]*filter-card[^"]*"[^>]*>.*?<select', html, re.DOTALL)))

idx = html.find("tp-compact-filter-grid")
print(html[idx:idx+1000])
