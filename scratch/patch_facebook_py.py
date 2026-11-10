fpath = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\fb_leads\facebook.py'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''def sync_page_leads(page_id):
    """Pull leads for a specific Facebook Page. Returns new count."""
    token = get_token_for_page(page_id)
    new_count = 0
    forms = _get(f"{page_id}/leadgen_forms", {"fields": "id,name", "limit": 100}, token=token)
    for form in forms.get("data", []):
        url_path, params = f"{form['id']}/leads", {"fields": LEAD_FIELDS, "limit": 100}
        while True:
            page = _get(url_path, params, token=token)
            for lead in page.get("data", []):
                _, created = save_lead(lead, page_id=page_id, form_name=form.get("name", ""))
                new_count += int(created)
            after = page.get("paging", {}).get("cursors", {}).get("after")
            if not page.get("paging", {}).get("next") or not after:
                break
            params = {"fields": LEAD_FIELDS, "limit": 100, "after": after}

    FacebookPage.objects.filter(page_id=page_id).update(
        last_sync_at=timezone.now(),
        last_sync_status=f"Synced {new_count} new leads",
        last_error=""
    )
    return new_count


def sync_all_leads():
    """Pull every lead from every connected Page or default page. Returns total new count."""
    connected_pages = FacebookPage.objects.filter(status='CONNECTED')
    total_new = 0
    if connected_pages.exists():
        for p in connected_pages:
            try:
                total_new += sync_page_leads(p.page_id)
            except Exception as e:
                log.warning("Failed to sync leads for page %s: %s", p.page_id, e)
        return total_new

    # Fallback to single page settings
    page_id = settings.FB_PAGE_ID
    return sync_page_leads(page_id)'''

replacement = '''def _to_timestamp(val, is_end_of_day=False):
    """Converts a datetime, date, Unix timestamp, or string into an integer Unix timestamp."""
    if not val:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        if val.isdigit():
            return int(val)
        from django.utils.dateparse import parse_date, parse_datetime
        import datetime
        dt = parse_datetime(val)
        if not dt:
            d = parse_date(val)
            if d:
                t = datetime.time.max if is_end_of_day else datetime.time.min
                dt = datetime.datetime.combine(d, t)
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
        if dt:
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            return int(dt.timestamp())
    elif hasattr(val, 'timestamp'):  # datetime
        if timezone.is_naive(val):
            val = timezone.make_aware(val, timezone.get_current_timezone())
        return int(val.timestamp())
    elif hasattr(val, 'year'):  # date
        import datetime
        t = datetime.time.max if is_end_of_day else datetime.time.min
        dt = datetime.datetime.combine(val, t)
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return int(dt.timestamp())
    return None


def sync_page_leads(page_id, since=None, until=None):
    """
    Pull leads for a specific Facebook Page with optional time boundaries.
    Parameters:
      since: Earliest lead creation time (datetime, date, timestamp, or YYYY-MM-DD str).
      until: Latest lead creation time (datetime, date, timestamp, or YYYY-MM-DD str).
    Returns count of newly created leads.
    """
    token = get_token_for_page(page_id)
    new_count = 0

    # Calculate effective since timestamp, honoring page cutoff date if configured
    since_ts = _to_timestamp(since, is_end_of_day=False)
    until_ts = _to_timestamp(until, is_end_of_day=True)

    fb_page = FacebookPage.objects.filter(page_id=page_id).first()
    if fb_page and getattr(fb_page, 'sync_cutoff_date', None):
        cutoff_ts = _to_timestamp(fb_page.sync_cutoff_date, is_end_of_day=False)
        if cutoff_ts:
            since_ts = max(since_ts, cutoff_ts) if since_ts else cutoff_ts

    forms = _get(f"{page_id}/leadgen_forms", {"fields": "id,name", "limit": 100}, token=token)
    for form in forms.get("data", []):
        url_path = f"{form['id']}/leads"
        params = {"fields": LEAD_FIELDS, "limit": 100}
        if since_ts:
            params["since"] = since_ts
        if until_ts:
            params["until"] = until_ts

        halt_form_paging = False
        while not halt_form_paging:
            page = _get(url_path, params, token=token)
            leads_data = page.get("data", [])
            for lead in leads_data:
                # Client-side time check
                c_time = lead.get("created_time")
                if c_time:
                    lead_dt = parse_datetime(c_time)
                    if lead_dt:
                        if timezone.is_naive(lead_dt):
                            lead_dt = timezone.make_aware(lead_dt, timezone.utc)
                        lead_ts = int(lead_dt.timestamp())
                        # If lead is older than since_ts, stop paging (Facebook returns newest first)
                        if since_ts and lead_ts < since_ts:
                            halt_form_paging = True
                            continue
                        if until_ts and lead_ts > until_ts:
                            continue

                _, created = save_lead(lead, page_id=page_id, form_name=form.get("name", ""))
                new_count += int(created)

            after = page.get("paging", {}).get("cursors", {}).get("after")
            if not page.get("paging", {}).get("next") or not after or halt_form_paging:
                break
            params = {"fields": LEAD_FIELDS, "limit": 100, "after": after}
            if since_ts:
                params["since"] = since_ts
            if until_ts:
                params["until"] = until_ts

    FacebookPage.objects.filter(page_id=page_id).update(
        last_sync_at=timezone.now(),
        last_sync_status=f"Synced {new_count} new leads",
        last_error=""
    )
    return new_count


def sync_all_leads(since=None, until=None):
    """Pull leads from every connected Page or default page with optional time boundaries. Returns total new count."""
    connected_pages = FacebookPage.objects.filter(status='CONNECTED')
    total_new = 0
    if connected_pages.exists():
        for p in connected_pages:
            try:
                total_new += sync_page_leads(p.page_id, since=since, until=until)
            except Exception as e:
                log.warning("Failed to sync leads for page %s: %s", p.page_id, e)
        return total_new

    # Fallback to single page settings
    page_id = settings.FB_PAGE_ID
    return sync_page_leads(page_id, since=since, until=until)'''

# Normalize newlines
c_norm = content.replace('\r\n', '\n')
t_norm = target.replace('\r\n', '\n')
r_norm = replacement.replace('\r\n', '\n')

if t_norm in c_norm:
    c_new = c_norm.replace(t_norm, r_norm)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(c_new)
    print('Updated facebook.py successfully')
else:
    print('Target not found in facebook.py')
