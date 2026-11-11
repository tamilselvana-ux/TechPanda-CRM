import os, sys, django
sys.path.insert(0, r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User, UserRole
from leads.models import Lead, WalkinEnquiryForm

print("=== USERS BY ROLE ===")
for role_val, role_label in UserRole.choices:
    u = User.objects.filter(role=role_val, is_active=True).first()
    print(f"  {role_val:15}: {u.username if u else 'NONE'}")

sample_lead = Lead.objects.first()
print("Sample lead ID:", sample_lead.pk if sample_lead else None)
walkin_form = WalkinEnquiryForm.objects.first()
print("Sample walkin form ID:", walkin_form.pk if walkin_form else None)
