import os
import time
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv('CRM/.env')
token = os.getenv('TELECRM_TOKEN')
ent_id = os.getenv('TELECRM_ENTERPRISE_ID')
base_url = f'https://next.telecrm.in/autoupdate/v2/enterprise/{ent_id}'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("Starting 1,000-lead sample timeline analysis...")

# 1. Fetch 1,000 leads (in 10 pages of 100)
all_leads = []
for page in range(10):
    skip = page * 100
    res = requests.post(
        f'{base_url}/lead/search',
        headers=headers,
        params={'skip': skip, 'limit': 100},
        json={}
    )
    if res.status_code != 200:
        print(f"Error fetching page {page}: {res.status_code}")
        break
    data = res.json().get('data', [])
    all_leads.extend(data)
    if len(data) < 100:
        break
    time.sleep(0.3)

print(f"Fetched {len(all_leads)} leads for timeline analysis.")

# 2. Query actions for each lead using ThreadPoolExecutor (max 5 workers to be polite to TeleCRM API)
stats = {
    'total_leads_sampled': len(all_leads),
    'leads_with_any_actions': 0,
    'leads_with_calls': 0,
    'total_actions': 0,
    'total_calls': 0,
    'total_outgoing_calls': 0,
    'total_incoming_calls': 0,
    'total_missed_calls': 0,
    'total_connected_calls': 0,
    'total_call_duration_sec': 0,
    'total_recordings_count': 0,
    'total_user_notes': 0,
    'total_system_notes': 0,
    'total_whatsapp_messages': 0,
    'total_facebook_actions': 0,
    'total_task_actions': 0,
    'action_type_histogram': {},
}

def analyze_lead(lead):
    lid = lead.get('id')
    try:
        r = requests.get(
            f'{base_url}/lead/{lid}?includeActions=true&limit=100',
            headers=headers,
            timeout=30
        )
        if r.status_code == 200:
            actions = r.json().get('actions', [])
            return lid, actions
    except Exception as e:
        return lid, []
    return lid, []

start_time = time.time()
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(analyze_lead, l) for l in all_leads]
    completed = 0
    for f in as_completed(futures):
        lid, actions = f.result()
        completed += 1
        if completed % 100 == 0:
            print(f"Processed {completed}/{len(all_leads)} lead timelines...")
        
        if actions:
            stats['leads_with_any_actions'] += 1
            has_call = False
            for a in actions:
                stats['total_actions'] += 1
                atype = a.get('type', 'UNKNOWN')
                stats['action_type_histogram'][atype] = stats['action_type_histogram'].get(atype, 0) + 1

                if atype in ('OUTGOING_CALL', 'INCOMING_CALL', 'MISSED_CALL'):
                    has_call = True
                    stats['total_calls'] += 1
                    dur = int(a.get('duration') or 0)
                    stats['total_call_duration_sec'] += dur
                    if dur > 0 or a.get('feedback') == 'CONNECTED':
                        stats['total_connected_calls'] += 1
                    if atype == 'OUTGOING_CALL':
                        stats['total_outgoing_calls'] += 1
                    elif atype == 'INCOMING_CALL':
                        stats['total_incoming_calls'] += 1
                    elif atype == 'MISSED_CALL':
                        stats['total_missed_calls'] += 1
                    
                    rec = a.get('callRecording')
                    if rec:
                        stats['total_recordings_count'] += 1
                elif atype == 'USER_NOTE':
                    stats['total_user_notes'] += 1
                elif atype == 'SYSTEM_NOTE':
                    stats['total_system_notes'] += 1
                elif atype in ('OUTGOING_WHATSAPP_MSG', 'INCOMING_WHATSAPP_MSG'):
                    stats['total_whatsapp_messages'] += 1
                elif atype == 'FACEBOOK':
                    stats['total_facebook_actions'] += 1
                elif atype == 'TASK_CREATION_ACTION':
                    stats['total_task_actions'] += 1

            if has_call:
                stats['leads_with_calls'] += 1

elapsed = time.time() - start_time
stats['analysis_duration_sec'] = round(elapsed, 2)

# Save result to json
with open('CRM/scratch_1000_sample_stats.json', 'w') as out_f:
    json.dump(stats, out_f, indent=2)

print("\n=== 1,000-LEAD TIMELINE SAMPLE RESULTS ===")
print(json.dumps(stats, indent=2))
