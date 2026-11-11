import os, sys, django
sys.path.insert(0, r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from leads.models import Lead, LeadStatus, LeadInterestType
print("LeadStatus:", [c[0] for c in LeadStatus.choices])
print("LeadInterestType:", [c[0] for c in LeadInterestType.choices])

# Look at fields of Lead
print("\nLead fields related to type, source, training, placement:")
for field in Lead._meta.get_fields():
    if field.name in ['lead_type', 'source', 'channel', 'product', 'sub_status', 'interest_type', 'enrollment', 'is_admitted', 'training_status', 'placement_status']:
        print(f" - {field.name}: {field.get_internal_type()} (choices: {getattr(field, 'choices', None)})")
