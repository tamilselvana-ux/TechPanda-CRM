import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import requests
from dotenv import load_dotenv

load_dotenv('CRM/.env')
token = os.getenv('TELECRM_TOKEN')
ent_id = os.getenv('TELECRM_ENTERPRISE_ID')
base_url = f'https://next.telecrm.in/autoupdate/v2/enterprise/{ent_id}'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

cfr = requests.get(f'{base_url}/custom-fields', headers=headers)
c_data = cfr.json() if isinstance(cfr.json(), list) else cfr.json().get('data', [])

car = requests.get(f'{base_url}/custom-actions', headers=headers)
ca_data = car.json() if isinstance(car.json(), list) else car.json().get('data', [])

print(f"=== ALL {len(c_data)} CUSTOM FIELDS ===")
for i, cf in enumerate(c_data, 1):
    print(f"{i:>2}. apiName: {cf.get('apiName')!r:35} | label: {cf.get('label')!r:30} | type: {cf.get('type')!r:15} | options: {len(cf.get('options') or [])}")

print(f"\n=== ALL {len(ca_data)} CUSTOM ACTION TYPES ===")
for i, ca in enumerate(ca_data, 1):
    print(f"{i:>2}. code: {ca.get('code')!r:15} | name: {ca.get('name')!r:20} | fields: {len(ca.get('fields') or [])}")
