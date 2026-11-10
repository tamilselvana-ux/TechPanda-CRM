import os, sys, django
sys.path.insert(0, r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from fb_leads.models import FacebookLead

admin = User.objects.filter(is_superuser=True).first()
if not admin:
    admin = User.objects.filter(role='ADMIN').first()

now = timezone.now()
today_str = now.strftime('%Y-%m-%d')
past_str = (now - timedelta(days=10)).strftime('%Y-%m-%d')

# Clean existing test leads if any
FacebookLead.objects.filter(leadgen_id__startswith='test_date_').delete()

# Create 2 leads: 1 today, 1 10 days ago
lead_today = FacebookLead.objects.create(
    leadgen_id='test_date_today',
    full_name='Test Today Lead',
    phone='9999900001',
    created_on_facebook=now
)
lead_past = FacebookLead.objects.create(
    leadgen_id='test_date_past',
    full_name='Test Past Lead',
    phone='9999900002',
    created_on_facebook=now - timedelta(days=10)
)

client = Client()
client.force_login(admin)

# Test 1: date_from=today should only return lead_today
resp = client.get(f'/facebook-leads/?date_from={today_str}')
assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
content1 = resp.content.decode()
assert 'Test Today Lead' in content1, 'lead_today must be in response'
assert 'Test Past Lead' not in content1, 'lead_past must NOT be in response'

# Test 2: date_to=past_str should only return lead_past
resp2 = client.get(f'/facebook-leads/?date_to={past_str}')
assert resp2.status_code == 200
content2 = resp2.content.decode()
assert 'Test Past Lead' in content2, 'lead_past must be in response'
assert 'Test Today Lead' not in content2, 'lead_today must NOT be in response'

# Test 3: API endpoint honors date_from
resp3 = client.get(f'/facebook-leads/api/recent/?date_from={today_str}')
assert resp3.status_code == 200
import json
data3 = json.loads(resp3.content.decode())
lead_names = [l['full_name'] for l in data3['leads']]
assert 'Test Today Lead' in lead_names, 'Test Today Lead should be in API results'
assert 'Test Past Lead' not in lead_names, 'Test Past Lead should NOT be in API results'

# Cleanup
FacebookLead.objects.filter(leadgen_id__startswith='test_date_').delete()

print('ALL ITEM 163 TESTS PASSED 100%!')
