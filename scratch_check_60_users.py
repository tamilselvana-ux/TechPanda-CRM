import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import requests
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv('CRM/.env')
token = os.getenv('TELECRM_TOKEN')
ent_id = os.getenv('TELECRM_ENTERPRISE_ID')
base_url = f'https://next.telecrm.in/autoupdate/v2/enterprise/{ent_id}'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

all_members = []
skip = 0
while True:
    res = requests.get(f'{base_url}/team-members?skip={skip}&limit=10', headers=headers).json()
    data = res.get('data', [])
    if not data: break
    all_members.extend(data)
    skip += len(data)
    if skip >= res.get('total_count', 0) or len(data) < 10: break

# Categorize managers
teams = defaultdict(list)
for m in all_members:
    mgr_email = (m.get('manager_email') or 'NO_MANAGER').strip().lower()
    mgr_name = m.get('manager_name') or 'Top-level / Self'
    teams[(mgr_name, mgr_email)].append(m)

print(f"Total Team Members: {len(all_members)}")
print(f"Total Reporting Groups: {len(teams)}\n")

for (m_name, m_email), members in sorted(teams.items(), key=lambda x: -len(x[1])):
    print(f"=== Team: {m_name} <{m_email}> ({len(members)} members) ===")
    for m in members:
        print(f"  - {m.get('name')} <{m.get('email')}> | Perm: {m.get('permission_template_name')} | Status: {m.get('status')}")

# Identify 17 Central users (those without branch suffixes _VEL, _TN, _AN, _CMB, _PR, _TM)
print("\n=== All Central Users (No branch suffix in name) ===")
central_users = []
for m in all_members:
    name = m.get('name', '')
    has_suffix = any(name.endswith(sfx) or f'{sfx} ' in name for sfx in ['_VEL', '_TN', '_AN', '_CMB', '_PR', '_TM'])
    if not has_suffix:
        central_users.append(m)

print(f"Count of Central Users: {len(central_users)}")
for idx, cu in enumerate(central_users, 1):
    print(f"{idx:>2}. {cu.get('name')} <{cu.get('email')}> | Role: {cu.get('permission_template_name')} | Manager: {cu.get('manager_name')} <{cu.get('manager_email')}>")
