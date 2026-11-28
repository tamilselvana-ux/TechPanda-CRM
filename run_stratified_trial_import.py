import os
import sys
import time
import json
import logging
from collections import defaultdict, Counter
from datetime import timedelta
from typing import Dict, List, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from accounts.models import UserRole
from branches.models import Branch
from calls.models import CallHistory
from drive.models import CallRecording
from followups.models import FollowUp, FollowUpStatus
from leads.models import Lead
from telecrm_sync.client import TeleCRMClient
from telecrm_sync.mapper import (
    KOLKATA_TZ,
    ingest_lead_actions,
    ingest_or_merge_lead,
    ms_to_datetime,
    parse_telecrm_phone,
    suppress_sync_side_effects,
)
from telecrm_sync.models import TeleCRMLead, TeleCRMUser

logger = logging.getLogger(__name__)
User = get_user_model()

trial_wall_start = time.time()

# Fail-safe check: Ensure we are operating on crmlive_trial
active_db = settings.DATABASES['default']['NAME']
print(f"Active Database: {active_db}", flush=True)
if active_db != 'crmlive_trial':
    print(f"FATAL SAFETY STOP: Active database is '{active_db}', expected 'crmlive_trial'. Aborting.", flush=True)
    sys.exit(1)

baseline = {
    "leads": Lead.objects.count(),
    "telecrm_leads": TeleCRMLead.objects.count(),
    "calls": CallHistory.objects.count(),
    "recordings": CallRecording.objects.count(),
    "followups": FollowUp.objects.count(),
    "users": User.objects.count(),
}
print(f"Baseline DB counts before trial: {baseline}", flush=True)

client = TeleCRMClient()

# 1. Reconcile team members (excluding murad.ali@telecrm.in and mohd.ozair@telecrm.in)
print("\n[Phase 1] Reconciling Confirmed Team Members...", flush=True)
team_members = client.get_team_members(include_deleted=False)
branch_map = {b.name.lower(): b for b in Branch.objects.all()}

def get_branch_obj(bname):
    low = bname.lower()
    for k, v in branch_map.items():
        if low in k or k in low:
            return v
    return None

created_users_count = 0
updated_users_count = 0

for m in team_members:
    email = (m.get('email') or '').strip().lower()
    name = (m.get('name') or '').strip()
    perm = (m.get('permission_template_name') or '').lower()
    mgr = (m.get('manager_name') or '').strip()
    uid = str(m.get('uid') or m.get('id') or m.get('userId') or '').strip()

    if email in ('murad.ali@telecrm.in', 'mohd.ozair@telecrm.in') or 'telecrm.in' in email:
        system_user, _ = User.objects.get_or_create(
            username='telecrm_system',
            defaults={
                'email': 'system@telecrm.internal',
                'first_name': 'TeleCRM',
                'last_name': 'System',
                'is_active': False,
                'role': UserRole.TELECALLER,
            }
        )
        if uid:
            TeleCRMUser.objects.update_or_create(
                uid=uid,
                defaults={'email': email, 'name': name, 'crm_user': system_user}
            )
        continue

    branch_name = ''
    for token, bname in [('_tn', 'T. Nagar'), ('_vel', 'Velachery'), ('velachery', 'Velachery'),
                         ('_cmb', 'Coimbatore'), ('_an', 'Anna Nagar'), ('_pr', 'Porur'),
                         ('_tm', 'Tambaram'), ('sholinganallur', 'Sholinganallur')]:
        if token in name.lower() or token in mgr.lower():
            branch_name = bname
            break

    role = UserRole.TELECALLER
    if 'root' in perm or 'admin' in perm or email == 'sarathbabu113@gmail.com':
        role = UserRole.SUPERADMIN
    elif 'manager' in perm:
        if mgr in ('Top Level', '', 'None') or 'sholinganallur' in name.lower() or email in ('sugashini.thangaraj@itechpanda.com', 'rashid.tc@itechpanda.com'):
            role = UserRole.SALES_HEAD
        elif any(sub in name for sub in ['Arshiya', 'swathi', 'Lavanya', 'Thangaraj', 'Srija', 'Vijaya', 'Venmani']):
            role = UserRole.BRANCH_HEAD
        else:
            role = UserRole.COUNSELOR

    branch_obj = get_branch_obj(branch_name) if branch_name else None
    username = email.split('@')[0].replace('.', '_').lower() if email else f"tc_{name.replace(' ', '_').lower()}"

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = User.objects.create(
            username=username,
            email=email,
            first_name=name.split()[0] if name else 'TeleCRM',
            last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else 'User',
            role=role,
            branch=branch_obj,
            is_active=False,
        )
        user.set_unusable_password()
        user.save()
        created_users_count += 1
    else:
        updated = False
        if not user.branch and branch_obj:
            user.branch = branch_obj
            updated = True
        if user.role != role and user.role == UserRole.TELECALLER:
            user.role = role
            updated = True
        if updated:
            user.save()
            updated_users_count += 1

    if uid:
        TeleCRMUser.objects.update_or_create(
            uid=uid,
            defaults={'email': email, 'name': name, 'crm_user': user}
        )

# Deactivate legacy test accounts
test_usernames = ['ravi_tc', 'meena_tc', 'suresh_tc', 'priya_tc', 'karthik_tc', 'rec_annanagar', 'kasi.s']
deactivated_test_count = User.objects.filter(username__in=test_usernames, is_active=True).update(is_active=False)
print(f"Users Reconciled: {created_users_count} created (inactive, unusable password), {updated_users_count} updated, {deactivated_test_count} test accounts deactivated. Total users: {User.objects.count()}", flush=True)

# 2. Stratified 500-Lead Selection
print("\n[Phase 2] Gathering Stratified 500-Lead Sample from TeleCRM...", flush=True)
stratified_leads: Dict[str, Dict[str, Any]] = {}
group_membership: Dict[str, str] = {}
sample_lead_ids_by_group: Dict[str, List[str]] = defaultdict(list)

def add_lead_to_sample(raw_l: Dict[str, Any], group: str, max_group: int):
    lid = str(raw_l.get('id') or raw_l.get('lead_id') or '').strip()
    if not lid or lid in stratified_leads or len(sample_lead_ids_by_group[group]) >= max_group:
        return False
    stratified_leads[lid] = raw_l
    group_membership[lid] = group
    sample_lead_ids_by_group[group].append(lid)
    return True

# Group 1: 100 newest
res1 = client._request("POST", "/lead/search", params={"skip": 0, "limit": 100}, json_data={})
for l in (res1.get('data', []) if isinstance(res1, dict) else res1):
    add_lead_to_sample(l, "100 Newest Leads", 100)
print(f"  -> Group 1 (Newest): {len(sample_lead_ids_by_group['100 Newest Leads'])}", flush=True)

# Group 3: 50 Won
won_statuses = ['Won_Velachery', 'WON_Sholinganallur', 'Won_Porur', 'Won_Anna Nagar', 'Won_Tambaram', 'Won_Coimbatore', 'Won_TNagar']
res3 = client._request("POST", "/lead/search", params={"skip": 0, "limit": 60}, json_data={"fields": {"status": won_statuses}})
for l in (res3.get('data', []) if isinstance(res3, dict) else res3):
    add_lead_to_sample(l, "50 Won Leads", 50)
print(f"  -> Group 3 (Won): {len(sample_lead_ids_by_group['50 Won Leads'])}", flush=True)

# Group 4: 50 Centre visited
cv_statuses = ['Centre visited', 'Center visited _ Anna nagar', 'Center visited _ Velachery', 'Center visited _ T Nagar', 'Center visited _ Tambaram', 'Center visited _ Sholinganallur', 'Center visited _ Coimbatore']
res4 = client._request("POST", "/lead/search", params={"skip": 0, "limit": 60}, json_data={"fields": {"status": cv_statuses}})
for l in (res4.get('data', []) if isinstance(res4, dict) else res4):
    add_lead_to_sample(l, "50 Centre Visited Leads", 50)
print(f"  -> Group 4 (Centre Visited): {len(sample_lead_ids_by_group['50 Centre Visited Leads'])}", flush=True)

# Group 5: 50 Call not picked 3+
cnp_statuses = ['Call not picked_3', 'Call not picked_4', 'Call not picked_5', 'Call not connected_3', 'Call not connected_4', 'Call not connected_5']
res5 = client._request("POST", "/lead/search", params={"skip": 0, "limit": 60}, json_data={"fields": {"status": cnp_statuses}})
for l in (res5.get('data', []) if isinstance(res5, dict) else res5):
    add_lead_to_sample(l, "50 Call Not Picked 3+ (RNR)", 50)
print(f"  -> Group 5 (RNR 3+): {len(sample_lead_ids_by_group['50 Call Not Picked 3+ (RNR)'])}", flush=True)

# Group 6: 50 Merged leads (matching existing CRM phones)
crm_phones = list(Lead.objects.values_list('normalized_phone', flat=True))
clean_crm_phones = []
for p in crm_phones:
    digits = ''.join(c for c in (p or '') if c.isdigit())
    if len(digits) == 10:
        clean_crm_phones.append('91' + digits)
    elif len(digits) == 12 and digits.startswith('91'):
        clean_crm_phones.append(digits)

for i in range(0, min(len(clean_crm_phones), 400), 100):
    if len(sample_lead_ids_by_group['50 Merged Leads']) >= 50:
        break
    res6 = client._request("POST", "/lead/search", params={"skip": 0, "limit": 60}, json_data={"fields": {"phone": clean_crm_phones[i:i+100]}})
    for l in (res6.get('data', []) if isinstance(res6, dict) else res6):
        add_lead_to_sample(l, "50 Merged Leads", 50)
print(f"  -> Group 6 (Merged): {len(sample_lead_ids_by_group['50 Merged Leads'])}", flush=True)

# Group 2: 100 leads with calls + recordings
call_search_skip = 0
while len(sample_lead_ids_by_group["100 with Calls + Recordings"]) < 100 and call_search_skip < 2000:
    res2 = client._request("POST", "/lead/search", params={"skip": call_search_skip, "limit": 50}, json_data={"fields": {"status": ["Call Taken", "Interested", "Hot", "Demo Attended", "Online Counselling Done"]}})
    call_candidates = res2.get('data', []) if isinstance(res2, dict) else res2
    if not call_candidates:
        break
    for cand in call_candidates:
        cid = cand.get('id')
        if not cid or cid in stratified_leads:
            continue
        try:
            c_actions, _ = client.get_lead_actions(cid, skip=0, limit=20)
            if any(a.get('type') in ('OUTGOING_CALL', 'INCOMING_CALL') and a.get('callRecording') for a in c_actions):
                add_lead_to_sample(cand, "100 with Calls + Recordings", 100)
                if len(sample_lead_ids_by_group["100 with Calls + Recordings"]) >= 100:
                    break
        except Exception:
            pass
    call_search_skip += 50
print(f"  -> Group 2 (Calls + Recordings): {len(sample_lead_ids_by_group['100 with Calls + Recordings'])}", flush=True)

# Group 7: 100 Random
for rand_skip in (12000, 12100):
    if len(sample_lead_ids_by_group['100 Random Leads']) >= 100:
        break
    res7 = client._request("POST", "/lead/search", params={"skip": rand_skip, "limit": 100}, json_data={})
    for l in (res7.get('data', []) if isinstance(res7, dict) else res7):
        add_lead_to_sample(l, "100 Random Leads", 100)
print(f"  -> Group 7 (Random): {len(sample_lead_ids_by_group['100 Random Leads'])}", flush=True)

total_selected = len(stratified_leads)
print(f"Total Unique Leads Selected for Trial: {total_selected}", flush=True)

# Snapshot BEFORE values for up to 5 merged leads in Group 6
merged_before_snapshots = {}
for lid in sample_lead_ids_by_group['50 Merged Leads'][:10]:
    raw_l = stratified_leads[lid]
    _, norm_p, _ = parse_telecrm_phone((raw_l.get('fields') or {}).get('phone'), lid)
    existing = None
    m_rec = TeleCRMLead.objects.filter(telecrm_id=lid).select_related('crm_lead').first()
    if m_rec and m_rec.crm_lead:
        existing = m_rec.crm_lead
    elif norm_p:
        existing = Lead.objects.filter(normalized_phone=norm_p).first()
    if existing:
        merged_before_snapshots[lid] = {
            "crm_id": existing.id,
            "name": existing.name,
            "phone": existing.phone,
            "email": existing.email,
            "status": existing.status,
            "branch": existing.branch.name if existing.branch else "Unknown",
            "branch_source": existing.branch_source,
            "calls_count": existing.calls.count(),
            "telecrm_id": (existing.custom_fields or {}).get("telecrm_id", ""),
        }

# 3. Execute Import on crmlive_trial
print("\n[Phase 3] Importing 500 Trial Leads & Downloading Recordings...", flush=True)
import_start = time.time()

leads_created = 0
leads_merged = 0
actions_mapped_total = 0
errors = []
recording_stats = {"downloaded": 0, "failed": 0, "pending": 0, "bytes": 0, "errors": []}
followup_stats = {"nfo_filled": 0, "pending": 0, "overdue": 0, "skipped_old": 0}
trial_crm_ids = []
user_cache: Dict[str, Any] = {}

today_ist = timezone.now().astimezone(KOLKATA_TZ).date()
cutoff_30d = today_ist - timedelta(days=30)

with suppress_sync_side_effects():
    for idx, (lid, raw_lead) in enumerate(stratified_leads.items(), 1):
        try:
            actions, _ = client.get_lead_actions(lid, skip=0, limit=100)
            nfo_ms = (raw_lead.get("fields") or {}).get("next_follow-up_on")
            f_dt = ms_to_datetime(nfo_ms)
            if f_dt:
                followup_stats["nfo_filled"] += 1
                f_date = f_dt.astimezone(KOLKATA_TZ).date()
                if f_date < cutoff_30d:
                    followup_stats["skipped_old"] += 1
                elif f_date < today_ist:
                    followup_stats["overdue"] += 1
                else:
                    followup_stats["pending"] += 1

            with transaction.atomic():
                lead, tc_mirror, was_created = ingest_or_merge_lead(
                    raw_lead=raw_lead,
                    actions=actions,
                    user_cache=user_cache
                )
                trial_crm_ids.append(lead.id)
                if was_created:
                    leads_created += 1
                else:
                    leads_merged += 1

                if actions:
                    mapped_cnt = ingest_lead_actions(
                        lead=lead,
                        tc_lead=tc_mirror,
                        raw_actions=actions,
                        user_cache=user_cache,
                        client=client,
                        recording_stats=recording_stats,
                        download_recordings=False,
                    )
                    actions_mapped_total += mapped_cnt
        except Exception as ex:
            logger.exception("Error importing trial lead %s: %s", lid, ex)
            errors.append({"lead_id": lid, "error": str(ex)})

        if idx % 50 == 0 or idx == total_selected:
            elapsed = time.time() - import_start
            print(
                f"  Progress: {idx}/{total_selected} | Created: {leads_created} | Merged: {leads_merged} | "
                f"Actions: {actions_mapped_total} | Recs DL: {recording_stats['downloaded']} / Fail: {recording_stats['failed']} | {elapsed:.1f}s",
                flush=True,
            )

total_trial_duration = time.time() - trial_wall_start

# Capture AFTER values for merged leads
merged_before_after = []
for lid, before in list(merged_before_snapshots.items())[:3]:
    cl = Lead.objects.get(id=before["crm_id"])
    merged_before_after.append({
        "telecrm_id": lid,
        "crm_id": cl.id,
        "before": before,
        "after": {
            "name": cl.name,
            "phone": cl.phone,
            "email": cl.email,
            "status": cl.status,
            "branch": cl.branch.name if cl.branch else "Unknown",
            "branch_source": cl.branch_source,
            "calls_count": cl.calls.count(),
            "telecrm_id": (cl.custom_fields or {}).get("telecrm_id", ""),
        }
    })

# Branch distribution & source counts across trial leads
trial_qs = Lead.objects.filter(id__in=trial_crm_ids)
branch_dist = Counter()
branch_source_dist = Counter()
for l in trial_qs.select_related("branch"):
    branch_dist[l.branch.name if l.branch else "Unknown"] += 1
    branch_source_dist[l.branch_source or "none"] += 1

# Invalid phones across trial leads
invalid_phones = []
for l in trial_qs.filter(phone_invalid=True):
    invalid_phones.append({
        "crm_id": l.id,
        "telecrm_id": (l.custom_fields or {}).get("telecrm_id", ""),
        "name": l.name,
        "raw_phone": l.phone,
    })

# Users list & vendor verification
murad_exists = User.objects.filter(email__iexact="murad.ali@telecrm.in").exists()
ozair_exists = User.objects.filter(email__iexact="mohd.ozair@telecrm.in").exists()
all_users = [
    {
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "branch": u.branch.name if u.branch else "Central / None",
        "is_active": u.is_active,
    }
    for u in User.objects.select_related("branch").order_by("id")
]

# Sample 10 per group
sample_records = []
for grp, ids in sample_lead_ids_by_group.items():
    for lid in ids[:10]:
        tc_lead_rec = TeleCRMLead.objects.filter(telecrm_id=lid).select_related('crm_lead').first()
        if tc_lead_rec and tc_lead_rec.crm_lead:
            cl = tc_lead_rec.crm_lead
            assignee = cl.assigned_telecaller or cl.assigned_counselor or cl.assigned_sales_head
            sample_records.append({
                "group": grp,
                "telecrm_id": lid,
                "crm_id": cl.id,
                "name": cl.name,
                "phone": cl.phone,
                "phone_invalid": cl.phone_invalid,
                "status": cl.status,
                "branch": cl.branch.name if cl.branch else "Unknown",
                "branch_source": cl.branch_source,
                "assignee": assignee.username if assignee else "None",
                "calls": cl.calls.count(),
                "recordings": cl.calls.exclude(recording_url='').count(),
                "followups": cl.followups.count(),
            })

# Extrapolate full-import time for 93,563 leads
per_lead_sec = total_trial_duration / max(1, total_selected)
est_full_hours = (per_lead_sec * 93563) / 3600.0

report_data = {
    "baseline": baseline,
    "trial_duration_sec": round(total_trial_duration, 2),
    "est_full_import_hours": round(est_full_hours, 2),
    "total_selected": total_selected,
    "leads_created": leads_created,
    "leads_merged": leads_merged,
    "actions_mapped": actions_mapped_total,
    "recording_stats": {
        "downloaded": recording_stats["downloaded"],
        "failed": recording_stats["failed"],
        "total_gb": round(recording_stats["bytes"] / (1024 ** 3), 6),
        "total_bytes": recording_stats["bytes"],
        "sample_errors": recording_stats["errors"][:5],
    },
    "followup_stats": followup_stats,
    "branch_distribution": dict(branch_dist),
    "branch_source_counts": dict(branch_source_dist),
    "invalid_phones_count": len(invalid_phones),
    "invalid_phones": invalid_phones,
    "merged_before_after": merged_before_after,
    "vendor_users_absent": {
        "murad_ali_exists": murad_exists,
        "mohd_ozair_exists": ozair_exists,
    },
    "total_users": len(all_users),
    "all_users": all_users,
    "db_totals_after": {
        "leads": Lead.objects.count(),
        "telecrm_leads": TeleCRMLead.objects.count(),
        "calls": CallHistory.objects.count(),
        "call_recordings_table": CallRecording.objects.count(),
        "followups": FollowUp.objects.count(),
    },
    "errors_count": len(errors),
    "samples": sample_records,
}

with open("CRM/scratch_trial_report.json", "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2, ensure_ascii=False)

print(f"\n=== TRIAL COMPLETE IN {total_trial_duration:.1f}s (Est full 93.5k: {est_full_hours:.2f} hrs) ===", flush=True)
print(f"Created: {leads_created} | Merged: {leads_merged} | Actions: {actions_mapped_total} | Errors: {len(errors)}", flush=True)
print(f"Recordings DL: {recording_stats['downloaded']} | Failed: {recording_stats['failed']} | GB: {report_data['recording_stats']['total_gb']}", flush=True)
print(f"Follow-ups -> Pending: {followup_stats['pending']} | Overdue: {followup_stats['overdue']} | Skipped (>30d): {followup_stats['skipped_old']}", flush=True)
print(f"Branch Source -> {dict(branch_source_dist)}", flush=True)
print(f"Invalid Phones -> {len(invalid_phones)}", flush=True)
