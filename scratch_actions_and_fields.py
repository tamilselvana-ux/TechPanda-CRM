import os
import requests
from dotenv import load_dotenv

load_dotenv('CRM/.env')
token = os.getenv('TELECRM_TOKEN')
ent_id = os.getenv('TELECRM_ENTERPRISE_ID')
base_url = f'https://next.telecrm.in/autoupdate/v2/enterprise/{ent_id}'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# 1. Custom Actions
car = requests.get(f'{base_url}/custom-actions', headers=headers)
ca_list = car.json() if isinstance(car.json(), list) else car.json().get('data', [])

print(f"=== CUSTOM ACTIONS ({len(ca_list)}) ===")
for a in ca_list:
    code = a.get('code')
    det = requests.get(f'{base_url}/custom-actions/{code}', headers=headers).json()
    print(f"Code: {code} | Name: {det.get('name') or a.get('name')} | Label: {det.get('label')} | Type: {det.get('type')} | Fields: {det.get('fields')}")

# 2. All 81 Custom Fields
cfr = requests.get(f'{base_url}/custom-fields', headers=headers)
cf_list = cfr.json() if isinstance(cfr.json(), list) else cfr.json().get('data', [])

print(f"\n=== ALL {len(cf_list)} CUSTOM FIELDS ===")
for idx, cf in enumerate(cf_list, 1):
    print(f"{idx:>2}. apiName: {cf.get('apiName')!r:35} | label: {cf.get('label')!r:32} | type: {cf.get('type')!r}")
