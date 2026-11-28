import os
import requests
import json
from dotenv import load_dotenv

load_dotenv('CRM/.env')
token = os.getenv('TELECRM_TOKEN')
ent_id = os.getenv('TELECRM_ENTERPRISE_ID')
base_url = f'https://next.telecrm.in/autoupdate/v2/enterprise/{ent_id}'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Fetch 100 leads
res = requests.post(f'{base_url}/lead/search', headers=headers, params={'skip': 0, 'limit': 100}, json={})
leads = res.json().get('data', [])
print(f"Fetched {len(leads)} leads")

call_sample = None
note_sample = None
payment_sample = None
whatsapp_sample = None
action_type_counts = {}

for l in leads:
    lid = l.get('id')
    lr = requests.get(f'{base_url}/lead/{lid}?includeActions=true&limit=100', headers=headers).json()
    actions = lr.get('actions', [])
    for a in actions:
        atype = a.get('type')
        action_type_counts[atype] = action_type_counts.get(atype, 0) + 1
        if atype == 'CALL' and not call_sample:
            call_sample = a
        elif atype == 'NOTE' and not note_sample:
            note_sample = a
        elif atype == 'PAYMENT' and not payment_sample:
            payment_sample = a
        elif atype in ('WHATSAPP', 'WHATSAPP_MESSAGE') and not whatsapp_sample:
            whatsapp_sample = a

print(f"Action type counts across {len(leads)} leads: {action_type_counts}")
if call_sample:
    print("\n=== SAMPLE CALL ACTION ===")
    print(json.dumps(call_sample, indent=2))
if note_sample:
    print("\n=== SAMPLE NOTE ACTION ===")
    print(json.dumps(note_sample, indent=2))
if payment_sample:
    print("\n=== SAMPLE PAYMENT ACTION ===")
    print(json.dumps(payment_sample, indent=2))
if whatsapp_sample:
    print("\n=== SAMPLE WHATSAPP ACTION ===")
    print(json.dumps(whatsapp_sample, indent=2))
