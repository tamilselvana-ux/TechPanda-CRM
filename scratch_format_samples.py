import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from telecrm_sync.models import TeleCRMLead
from leads.models import Lead

with open('CRM/scratch_trial_report.json') as f:
    rep = json.load(f)

samples = rep.get('samples', [])

# Pick 10 merged leads (crm_id <= 635)
merged_samples = []
for tl in TeleCRMLead.objects.filter(crm_lead__id__lte=635).select_related('crm_lead')[:10]:
    cl = tl.crm_lead
    call_cnt = cl.calls.count()
    rec_cnt = cl.calls.exclude(recording_url='').count()
    assignee = cl.assigned_telecaller or cl.assigned_counselor or cl.assigned_sales_head
    merged_samples.append({
        'group': '50 Merged Leads (Matching Phones)',
        'telecrm_id': tl.telecrm_id,
        'crm_id': cl.id,
        'name': cl.name,
        'phone': cl.phone,
        'status': cl.status,
        'branch': cl.branch.name if cl.branch else 'Unassigned',
        'assignee': assignee.username if assignee else 'None',
        'calls': call_cnt,
        'recordings': rec_cnt,
        'followups': cl.followups.count(),
        'visit_date': cl.visit_scheduled_date.strftime('%Y-%m-%d %H:%M') if cl.visit_scheduled_date else 'None',
        'dnc': cl.do_not_call,
    })

all_samples_by_group = {}
for s in samples:
    grp = s['group']
    all_samples_by_group.setdefault(grp, []).append(s)

all_samples_by_group['50 Merged Leads'] = merged_samples

for grp, items in all_samples_by_group.items():
    print(f"\n### Group: {grp}")
    print("| # | TeleCRM Lead ID | CRM ID | Lead Name | Phone | Status | Branch | Assignee | Calls (Rec) | FollowUps |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for idx, item in enumerate(items[:10], 1):
        tid = item['telecrm_id']
        cid = item['crm_id']
        name = item['name']
        phone = item['phone']
        st = item['status']
        br = item['branch']
        asn = item['assignee']
        calls = f"{item['calls']} ({item['recordings']})"
        fus = item['followups']
        print(f"| {idx} | `{tid}` | #{cid} | {name} | {phone} | {st} | {br} | {asn} | {calls} | {fus} |")
