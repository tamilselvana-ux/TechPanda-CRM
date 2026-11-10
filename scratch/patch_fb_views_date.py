import os

path = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\fb_leads\views.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add date_from and date_to to lead_list GET extraction
old1 = '''    q = request.GET.get("q", "").strip()
    selected_form = request.GET.get("form", "").strip()
    selected_ad = request.GET.get("ad", "").strip()
    crm_filter = request.GET.get("crm", "").strip()

    available_forms = list('''

new1 = '''    q = request.GET.get("q", "").strip()
    selected_form = request.GET.get("form", "").strip()
    selected_ad = request.GET.get("ad", "").strip()
    crm_filter = request.GET.get("crm", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    available_forms = list('''

assert old1 in content, "old1 not found"
content = content.replace(old1, new1, 1)

# 2. Add date_from and date_to query filtering to lead_list
old2 = '''    if selected_ad:
        ad_q = Q(ad_name=selected_ad) | Q(ad_id=selected_ad)
        leads = leads.filter(ad_q)
        base_qs = base_qs.filter(ad_q)

    if q:'''

new2 = '''    if selected_ad:
        ad_q = Q(ad_name=selected_ad) | Q(ad_id=selected_ad)
        leads = leads.filter(ad_q)
        base_qs = base_qs.filter(ad_q)

    if date_from:
        from_q = Q(created_on_facebook__date__gte=date_from) | Q(created_on_facebook__isnull=True, received_at__date__gte=date_from)
        leads = leads.filter(from_q)
        base_qs = base_qs.filter(from_q)

    if date_to:
        to_q = Q(created_on_facebook__date__lte=date_to) | Q(created_on_facebook__isnull=True, received_at__date__lte=date_to)
        leads = leads.filter(to_q)
        base_qs = base_qs.filter(to_q)

    if q:'''

assert old2 in content, "old2 not found"
content = content.replace(old2, new2, 1)

# 3. Add date_from and date_to to context
old3 = '''        "selected_form": selected_form,
        "selected_ad": selected_ad,
        "available_forms": available_forms,'''

new3 = '''        "selected_form": selected_form,
        "selected_ad": selected_ad,
        "date_from": date_from,
        "date_to": date_to,
        "available_forms": available_forms,'''

assert old3 in content, "old3 not found"
content = content.replace(old3, new3, 1)

# 4. In api_recent_leads
old4 = '''    selected_ad = request.GET.get("ad", "").strip()
    if selected_form:
        leads_qs = leads_qs.filter(Q(form_name=selected_form) | Q(form_id=selected_form))
    if selected_ad:
        leads_qs = leads_qs.filter(Q(ad_name=selected_ad) | Q(ad_id=selected_ad))
    if request.GET.get("crm") == "error":
        leads_qs = leads_qs.filter(crm_result="error")'''

new4 = '''    selected_ad = request.GET.get("ad", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    if selected_form:
        leads_qs = leads_qs.filter(Q(form_name=selected_form) | Q(form_id=selected_form))
    if selected_ad:
        leads_qs = leads_qs.filter(Q(ad_name=selected_ad) | Q(ad_id=selected_ad))
    if date_from:
        leads_qs = leads_qs.filter(Q(created_on_facebook__date__gte=date_from) | Q(created_on_facebook__isnull=True, received_at__date__gte=date_from))
    if date_to:
        leads_qs = leads_qs.filter(Q(created_on_facebook__date__lte=date_to) | Q(created_on_facebook__isnull=True, received_at__date__lte=date_to))
    if request.GET.get("crm") == "error":
        leads_qs = leads_qs.filter(crm_result="error")'''

assert old4 in content, "old4 not found"
content = content.replace(old4, new4, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched fb_leads/views.py")
