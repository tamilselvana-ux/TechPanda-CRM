import re

# 1. Update CRM/fb_leads/facebook.py
fb_py_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\fb_leads\facebook.py'
with open(fb_py_path, 'r', encoding='utf-8') as f:
    fb_code = f.read()

# Add platform to LEAD_FIELDS
if 'platform' not in fb_code.split('LEAD_FIELDS =')[1].split('\n')[0]:
    fb_code = fb_code.replace(
        'LEAD_FIELDS = "id,created_time,field_data,form_id,ad_id,ad_name,campaign_name"',
        'LEAD_FIELDS = "id,created_time,field_data,form_id,ad_id,ad_name,campaign_name,platform"'
    )

# Save platform in save_lead defaults
if '"platform":' not in fb_code:
    fb_code = fb_code.replace(
        '"campaign_name": lead.get("campaign_name", ""),',
        '"campaign_name": lead.get("campaign_name", ""),\n            "platform": (lead.get("platform") or "").strip(),'
    )

with open(fb_py_path, 'w', encoding='utf-8') as f:
    f.write(fb_code)
print('Updated fb_leads/facebook.py successfully')


# 2. Update CRM/fb_leads/crm.py
crm_py_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\fb_leads\crm.py'
with open(crm_py_path, 'r', encoding='utf-8') as f:
    crm_code = f.read()

helper_fn = '''
def resolve_meta_source_and_channel(fb_lead):
    """
    Distinguishes between Facebook and Instagram lead origins using:
    1. Meta Leadgen API 'platform' field ('fb' vs 'ig')
    2. Ad name / Campaign name / Form name mentioning 'instagram' or 'ig'
    3. Form answers mentioning Instagram handle or placement
    """
    platform_val = (getattr(fb_lead, 'platform', '') or '').strip().lower()
    corpus = f"{fb_lead.campaign_name or ''} {fb_lead.ad_name or ''} {fb_lead.form_name or ''}".lower()
    answers_corpus = ' '.join(str(v).lower() for v in (fb_lead.all_answers or {}).values())
    combined = f"{corpus} {answers_corpus}"

    if platform_val in ['ig', 'instagram'] or 'instagram' in combined or 'insta' in combined:
        return 'Instagram', 'Instagram', 'instagram', '📸 Instagram Lead Ad — '
    return 'Facebook', 'Facebook', 'facebook', '📘 Facebook Lead Ad — '
'''

if 'def resolve_meta_source_and_channel' not in crm_code:
    crm_code = crm_code.replace('CHANNEL = "Facebook"', 'CHANNEL = "Facebook"\n' + helper_fn)

old_intake_call = '''        lead, created = intake.intake_lead(
            phone=raw_phone,
            source=SOURCE,
            channel_name=CHANNEL,
            name=fb_lead.full_name,
            email=fb_lead.email,
            branch=branch_for(fb_lead),
            product=product_for(fb_lead),
            note="📘 Facebook Lead Ad — " + (_summary(fb_lead) or "new form submission"),
            provider_event_id=fb_lead.leadgen_id,
            incoming_timestamp=getattr(fb_lead, 'created_time', None),
            data_payload=payload,
        )

        from leads.qualification import autofill_lead_qualification
        autofill_lead_qualification(lead, payload, source='Facebook')'''

new_intake_call = '''        src_name, chan_name, plat_code, prefix = resolve_meta_source_and_channel(fb_lead)

        lead, created = intake.intake_lead(
            phone=raw_phone,
            source=src_name,
            channel_name=chan_name,
            platform=plat_code,
            name=fb_lead.full_name,
            email=fb_lead.email,
            branch=branch_for(fb_lead),
            product=product_for(fb_lead),
            note=prefix + (_summary(fb_lead) or "new form submission"),
            provider_event_id=fb_lead.leadgen_id,
            incoming_timestamp=getattr(fb_lead, 'created_time', None),
            data_payload=payload,
        )

        from leads.qualification import autofill_lead_qualification
        autofill_lead_qualification(lead, payload, source=src_name)'''

crm_code = crm_code.replace(old_intake_call, new_intake_call)

with open(crm_py_path, 'w', encoding='utf-8') as f:
    f.write(crm_code)
print('Updated fb_leads/crm.py successfully')


# 3. Update CRM/leads/intake.py
intake_py_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\intake.py'
with open(intake_py_path, 'r', encoding='utf-8') as f:
    intake_code = f.read()

# Add platform kwarg to intake_lead signature
if 'token_number=None,\n    platform=None,' not in intake_code:
    intake_code = intake_code.replace(
        'token_number=None,\n):',
        'token_number=None,\n    platform=None,\n):'
    )

# Infer and pass platform to Lead.objects.create
old_create = '''        lead = Lead.objects.create(
            name=clean_name or f"Lead ({fallback_disp})",
            phone=number or raw_phone,
            normalized_phone=norm_phone_val,
            alternate_phone=norm_alt,
            email=clean_email,
            channel=get_channel(channel_name) if channel_name else None,
            status=LeadStatus.NEW,
            source=source,
            is_offline=is_offline_lead,
            branch=branch,'''

new_create = '''        # Infer origin platform if not explicitly passed
        resolved_platform = platform
        if not resolved_platform:
            sl = (source or '').lower()
            cl = (channel_name or '').lower()
            if 'instagram' in sl or 'insta' in sl or 'instagram' in cl:
                resolved_platform = 'instagram'
            elif 'facebook' in sl or 'fb' in sl or 'meta' in sl or 'facebook' in cl:
                resolved_platform = 'facebook'
            elif 'whatsapp' in sl or 'whatsapp' in cl:
                resolved_platform = 'whatsapp'
            elif 'walk' in sl or 'walk' in cl:
                resolved_platform = 'direct'
            elif 'google' in sl or 'google' in cl:
                resolved_platform = 'google'
            else:
                resolved_platform = 'other'

        lead = Lead.objects.create(
            name=clean_name or f"Lead ({fallback_disp})",
            phone=number or raw_phone,
            normalized_phone=norm_phone_val,
            alternate_phone=norm_alt,
            email=clean_email,
            channel=get_channel(channel_name) if channel_name else None,
            status=LeadStatus.NEW,
            source=source,
            platform=resolved_platform,
            is_offline=is_offline_lead,
            branch=branch,'''

intake_code = intake_code.replace(old_create, new_create)

with open(intake_py_path, 'w', encoding='utf-8') as f:
    f.write(intake_code)
print('Updated leads/intake.py successfully')
