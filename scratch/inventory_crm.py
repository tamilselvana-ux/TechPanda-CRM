import os, sys, django
sys.path.insert(0, r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.apps import apps
from django.core.management import get_commands

print("=== INSTALLED APPS ===")
for app in settings.INSTALLED_APPS:
    print(" -", app)

print("\n=== MODELS BY LOCAL APP ===")
local_apps = [
    'accounts', 'activities', 'branches', 'branch_heads', 'calls', 'chat',
    'counselors', 'drive', 'fb_leads', 'finance', 'followups',
    'frontend_flow_builder', 'leads', 'lead_channels', 'managers', 'products',
    'reports', 'telecallers'
]
for app_label in local_apps:
    try:
        app_config = apps.get_app_config(app_label)
        models = [m.__name__ for m in app_config.get_models()]
        print(f" {app_label}: {models}")
    except LookupError:
        pass

print("\n=== LEAD STATUSES & TYPES ===")
from leads.models import LeadStatus, LeadType, LeadInterestType
print("LeadStatus:", LeadStatus.choices)
print("LeadType:", getattr(LeadType, 'choices', 'N/A'))
print("LeadInterestType:", getattr(LeadInterestType, 'choices', 'N/A'))

print("\n=== MANAGEMENT COMMANDS ===")
cmds = get_commands()
for name, app_name in sorted(cmds.items()):
    if app_name in local_apps or not app_name.startswith('django.'):
        print(f" {name} ({app_name})")
