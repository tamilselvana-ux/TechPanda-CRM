import os
import re

# 1. Update urls.py
urls_path = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\fb_leads\urls.py"
with open(urls_path, "r", encoding="utf-8") as f:
    urls_content = f.read()

cutoff_route = '    path("pages/<int:page_id>/cutoff/", views.fb_page_update_cutoff, name="fb_page_update_cutoff"),\n'
if "fb_page_update_cutoff" not in urls_content:
    urls_content = urls_content.replace(
        '    path("pages/<int:page_id>/sync/", views.fb_page_sync, name="fb_page_sync"),\n',
        '    path("pages/<int:page_id>/sync/", views.fb_page_sync, name="fb_page_sync"),\n' + cutoff_route
    )
    with open(urls_path, "w", encoding="utf-8") as f:
        f.write(urls_content)
    print("Updated fb_leads/urls.py")
else:
    print("urls.py already has cutoff route")

# 2. Update views.py
views_path = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\fb_leads\views.py"
with open(views_path, "r", encoding="utf-8") as f:
    views_content = f.read()

helper_and_views = '''def _parse_sync_time_range(request):
    """
    Parses sync_mode, start_date, and end_date from request.POST or request.GET.
    Returns (since_dt, until_dt, mode_label).
    """
    from django.utils import timezone
    from datetime import timedelta, datetime, time
    from django.utils.dateparse import parse_date

    mode = request.POST.get("sync_mode") or request.GET.get("sync_mode") or "today"
    start_str = request.POST.get("start_date") or request.GET.get("start_date") or ""
    end_str = request.POST.get("end_date") or request.GET.get("end_date") or ""

    now = timezone.now()
    today_start = timezone.make_aware(datetime.combine(now.date(), time.min), timezone.get_current_timezone())

    if mode == "today":
        return today_start, None, "Today"
    elif mode == "yesterday":
        yest_start = today_start - timedelta(days=1)
        return yest_start, None, "Yesterday & Today"
    elif mode == "7days":
        since_7d = now - timedelta(days=7)
        return since_7d, None, "Last 7 Days"
    elif mode == "custom":
        since_dt = None
        until_dt = None
        if start_str:
            d1 = parse_date(start_str.strip())
            if d1:
                since_dt = timezone.make_aware(datetime.combine(d1, time.min), timezone.get_current_timezone())
        if end_str:
            d2 = parse_date(end_str.strip())
            if d2:
                until_dt = timezone.make_aware(datetime.combine(d2, time.max), timezone.get_current_timezone())
        label = f"{start_str or 'Start'} to {end_str or 'Now'}"
        return since_dt, until_dt, label
    elif mode == "all":
        return None, None, "All Time"

    return today_start, None, "Today"


@login_required
@require_POST
def sync_leads(request):
    """Button: link the Page for automatic leads, then pull leads with optional date range."""
    if not _can_manage(request.user):
        raise PermissionDenied("Only Admin and Sales Head can sync Facebook leads.")
    try:
        if subscribe_page():
            messages.success(request, "Page linked: new Facebook leads will now arrive automatically.")
    except Exception as exc:
        messages.error(request, f"{exc}")

    since_dt, until_dt, mode_label = _parse_sync_time_range(request)

    try:
        n = sync_all_leads(since=since_dt, until=until_dt)
        messages.success(request, f"Sync done ({mode_label}). {n} new Facebook lead(s) added to the CRM.")
        log_activity(user=request.user, action="Facebook Leads Synced",
                     description=f"Facebook Lead Ads sync ({mode_label}): {n} new lead(s).", object_type="FacebookLead",
                     request=request)
    except Exception as exc:
        messages.error(request, f"Sync failed: {exc}")
    # Retry CRM creation for any Facebook lead that failed before (e.g. missing branch setup).
    for fb in FacebookLead.objects.filter(lead__isnull=True)[:500]:
        push_to_crm(fb)
    return redirect("fb_leads:facebook_leads")
'''

# Replace old sync_leads
old_sync_leads_pattern = r'@login_required\s+@require_POST\s+def sync_leads\(request\):[\s\S]*?return redirect\("fb_leads:facebook_leads"\)'
if re.search(old_sync_leads_pattern, views_content):
    views_content = re.sub(old_sync_leads_pattern, helper_and_views.strip(), views_content, count=1)
    print("Replaced sync_leads with date-aware version")

# Replace fb_page_sync with date-aware version
new_fb_page_sync = '''@login_required
@require_POST
def fb_page_sync(request, page_id):
    """Sync leads specifically for one Facebook Page (supports date range, form POST and AJAX)."""
    if not _can_manage(request.user):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
        raise PermissionDenied("Only Admin and Sales Head can sync leads.")

    from .models import FacebookPage
    from .scheduler import trigger_immediate_page_sync

    page = FacebookPage.objects.filter(id=page_id).first()
    if not page:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Facebook Page not found"}, status=404)
        messages.error(request, "Facebook Page not found.")
        return redirect("fb_leads:fb_accounts")

    since_dt, until_dt, mode_label = _parse_sync_time_range(request)

    try:
        n = trigger_immediate_page_sync(page.page_id, since=since_dt, until=until_dt)
        page.refresh_from_db()
        msg = f"Sync complete for '{page.page_name}' ({mode_label}): {n} new lead(s) imported."
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "message": msg,
                "new_leads": n,
                "last_sync_at": page.last_sync_at.strftime("%d %b, %H:%M") if page.last_sync_at else "Just now",
                "last_sync_status": page.last_sync_status,
                "next_sync_at": page.next_sync_at.strftime("%H:%M") if page.next_sync_at else "—",
            })
        messages.success(request, msg)
    except Exception as exc:
        err_msg = f"Sync failed for '{page.page_name}': {exc}"
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": err_msg}, status=500)
        messages.error(request, err_msg)

    return redirect("fb_leads:fb_accounts")


@login_required
@require_POST
def fb_page_update_cutoff(request, page_id):
    """Update historical lead sync cutoff date for a Facebook Page."""
    if not _can_manage(request.user):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
        raise PermissionDenied("Only Admin and Sales Head can change cutoff date.")

    from django.utils.dateparse import parse_date
    from .models import FacebookPage

    page = FacebookPage.objects.filter(id=page_id).first()
    if not page:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Facebook Page not found"}, status=404)
        messages.error(request, "Facebook Page not found.")
        return redirect("fb_leads:fb_accounts")

    cutoff_str = request.POST.get("sync_cutoff_date", "").strip()
    if cutoff_str:
        parsed_d = parse_date(cutoff_str)
        if not parsed_d:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": "Invalid date format (use YYYY-MM-DD)"}, status=400)
            messages.error(request, "Invalid date format.")
            return redirect("fb_leads:fb_accounts")
        page.sync_cutoff_date = parsed_d
        msg = f"Set lead sync cutoff to {parsed_d.strftime('%d %b %Y')} for '{page.page_name}'."
    else:
        page.sync_cutoff_date = None
        msg = f"Cleared sync cutoff date for '{page.page_name}'."

    page.save(update_fields=["sync_cutoff_date"])
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "sync_cutoff_date": str(page.sync_cutoff_date) if page.sync_cutoff_date else "",
            "message": msg,
        })
    messages.success(request, msg)
    return redirect("fb_leads:fb_accounts")
'''

old_page_sync_pattern = r'@login_required\s+@require_POST\s+def fb_page_sync\(request, page_id\):[\s\S]*?return redirect\("fb_leads:fb_accounts"\)'
if re.search(old_page_sync_pattern, views_content):
    views_content = re.sub(old_page_sync_pattern, new_fb_page_sync.strip(), views_content, count=1)
    print("Replaced fb_page_sync and added fb_page_update_cutoff")

with open(views_path, "w", encoding="utf-8") as f:
    f.write(views_content)
print("Updated fb_leads/views.py successfully")
