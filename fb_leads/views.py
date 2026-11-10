import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from activities.utils import log_activity

from .crm import push_to_crm
from .facebook import fetch_and_save_lead, subscribe_page, sync_all_leads
from .models import FacebookLead

log = logging.getLogger("crm")


def _can_manage(user):
    return user.is_authenticated and (user.is_admin_user or user.is_sales_head_user)


@csrf_exempt
def webhook(request):
    """
    Facebook calls this URL (also mounted at the CRM's old /api/webhooks/meta/leads/).
    GET = verification handshake, POST = new lead (only its id; full details are fetched from Graph API).
    """
    if request.method == "GET":
        q = request.GET
        mode = q.get("hub.mode") or q.get("hub_mode")
        received = (q.get("hub.verify_token") or q.get("hub_verify_token") or "").strip()
        challenge = q.get("hub.challenge") or q.get("hub_challenge") or ""
        expected = str(getattr(settings, "FB_VERIFY_TOKEN", "")).strip()
        if mode == "subscribe" and expected and received == expected:
            log.info("Facebook webhook verified")
            return HttpResponse(challenge)
        log.warning("Facebook webhook verification failed (check FB_VERIFY_TOKEN in .env)")
        return HttpResponse("Verification failed", status=403)

    if request.method != "POST":
        return HttpResponse(status=405)

    # Only accept messages really signed by Facebook with our App Secret.
    secret = getattr(settings, "FB_APP_SECRET", "") or ""
    if not secret:
        log.error("Facebook webhook rejected: FB_APP_SECRET is not set in .env")
        return HttpResponse("Not configured", status=403)
    signature = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        log.warning("Facebook webhook rejected: bad signature")
        return HttpResponse("Bad signature", status=403)

    try:
        payload = json.loads(request.body)
    except ValueError:
        return HttpResponse("Bad JSON", status=400)

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "leadgen":
                continue
            value = change.get("value", {})
            try:
                fetch_and_save_lead(value["leadgen_id"], page_id=value.get("page_id", ""))
            except Exception as exc:  # log it but still answer 200 so Facebook doesn't keep retrying
                log.exception("Could not save Facebook lead %s: %s", value.get("leadgen_id"), exc)
    return HttpResponse("OK")


@login_required
def lead_list(request):
    """All Facebook leads with search, form/ad filters, and clickable KPIs."""
    if not _can_manage(request.user):
        raise PermissionDenied("Only Admin and Sales Head can view Facebook leads.")
    q = request.GET.get("q", "").strip()
    selected_form = request.GET.get("form", "").strip()
    selected_ad = request.GET.get("ad", "").strip()
    crm_filter = request.GET.get("crm", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    available_forms = list(
        FacebookLead.objects.exclude(form_name__isnull=True).exclude(form_name="")
        .values_list("form_name", flat=True).distinct().order_by("form_name")
    )
    available_ads = list(
        FacebookLead.objects.exclude(ad_name__isnull=True).exclude(ad_name="")
        .values_list("ad_name", flat=True).distinct().order_by("ad_name")
    )

    leads = FacebookLead.objects.select_related("lead", "lead__assigned_telecaller", "lead__branch")
    base_qs = FacebookLead.objects.all()

    if selected_form:
        form_q = Q(form_name=selected_form) | Q(form_id=selected_form)
        leads = leads.filter(form_q)
        base_qs = base_qs.filter(form_q)

    if selected_ad:
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

    if q:
        search_q = (
            Q(full_name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q)
            | Q(form_name__icontains=q) | Q(ad_name__icontains=q) | Q(campaign_name__icontains=q)
        )
        leads = leads.filter(search_q)
        base_qs = base_qs.filter(search_q)

    total_kpi = base_qs.count()
    error_kpi = base_qs.filter(crm_result="error").count()

    if crm_filter == "error":
        leads = leads.filter(crm_result="error")

    page = Paginator(leads, 25).get_page(request.GET.get("page"))
    return render(request, "fb_leads/leads.html", {
        "page": page,
        "q": q,
        "selected_form": selected_form,
        "selected_ad": selected_ad,
        "date_from": date_from,
        "date_to": date_to,
        "available_forms": available_forms,
        "available_ads": available_ads,
        "crm_filter": crm_filter,
        "total": total_kpi,
        "errors": error_kpi,
        "configured": bool(getattr(settings, "FB_PAGE_TOKEN", "") and getattr(settings, "FB_PAGE_ID", "")),
        "lead_url_name": "admin_lead_detail" if request.user.is_admin_user else "manager_lead_detail",
    })


@login_required
def api_recent_leads(request):
    """
    Lightweight JSON endpoint for the Facebook Leads page live poll (Issue 2).
    Polls ONLY the local CRM database (never hits external Meta Graph API).
    Returns latest count, error count, and latest 25 leads.
    """
    from django.http import JsonResponse
    if not _can_manage(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    q = request.GET.get("q", "").strip()
    leads_qs = FacebookLead.objects.select_related("lead", "lead__assigned_telecaller", "lead__branch")
    if q:
        leads_qs = leads_qs.filter(
            Q(full_name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q)
            | Q(form_name__icontains=q) | Q(ad_name__icontains=q) | Q(campaign_name__icontains=q)
        )
    selected_form = request.GET.get("form", "").strip()
    selected_ad = request.GET.get("ad", "").strip()
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
        leads_qs = leads_qs.filter(crm_result="error")

    total_count = FacebookLead.objects.count()
    error_count = FacebookLead.objects.filter(crm_result="error").count()

    lead_url_name = "admin_lead_detail" if request.user.is_admin_user else "manager_lead_detail"
    from django.urls import reverse

    results = []
    for fb in leads_qs[:25]:
        lead_url = ""
        lead_info = None
        if fb.lead:
            try:
                lead_url = reverse(lead_url_name, args=[fb.lead.pk])
            except Exception:
                lead_url = f"/leads/{fb.lead.pk}/"
            
            telecaller_name = ""
            if fb.lead.assigned_telecaller:
                telecaller_name = fb.lead.assigned_telecaller.get_full_name() or fb.lead.assigned_telecaller.username
            else:
                telecaller_name = fb.lead.assignment_status or "Unassigned"

            lead_info = {
                "id": fb.lead.pk,
                "name": fb.lead.name,
                "url": lead_url,
                "branch": fb.lead.branch.name if fb.lead.branch else "No branch",
                "assigned_to": telecaller_name,
            }

        created_dt = fb.created_on_facebook or fb.received_at
        results.append({
            "id": fb.id,
            "leadgen_id": fb.leadgen_id,
            "full_name": fb.full_name or "—",
            "phone": fb.phone or "—",
            "email": fb.email or "",
            "form_name": fb.form_name or "—",
            "ad_name": fb.ad_name or "",
            "campaign_name": fb.campaign_name or "",
            "created_str": created_dt.strftime("%d %b %Y, %I:%M %p") if created_dt else "—",
            "crm_result": fb.crm_result,
            "crm_error": fb.crm_error,
            "lead": lead_info,
            "all_answers": fb.all_answers or {},
        })

    return JsonResponse({
        "success": True,
        "total": total_count,
        "errors": error_count,
        "leads": results,
    })


def _parse_sync_time_range(request):
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


@login_required
def fb_accounts(request):
    """View and manage multiple Facebook Accounts and their connected Facebook Pages."""
    if not _can_manage(request.user):
        raise PermissionDenied("Only Admin and Sales Head can manage Facebook connections.")

    from branches.models import Branch
    from .models import FacebookAccount, FacebookPage
    from .scheduler import ensure_scheduler_running

    ensure_scheduler_running()

    accounts = FacebookAccount.objects.prefetch_related("pages", "pages__branch").all()
    branches = Branch.objects.filter(status=Branch.Status.ACTIVE).order_by("name")

    return render(request, "fb_leads/accounts.html", {
        "accounts": accounts,
        "branches": branches,
        "interval_choices": FacebookPage.SYNC_INTERVAL_CHOICES,
        "env_configured": bool(getattr(settings, "FB_PAGE_TOKEN", "") and getattr(settings, "FB_PAGE_ID", "")),
        "app_id": getattr(settings, "FB_APP_ID", ""),
    })


@login_required
@require_POST
def fb_account_connect(request):
    """Add a new Facebook Account and automatically discover its Pages."""
    if not _can_manage(request.user):
        raise PermissionDenied("Only Admin and Sales Head can connect Facebook accounts.")

    from .models import FacebookAccount
    from .facebook import sync_pages_for_account

    account_name = request.POST.get("account_name", "").strip()
    access_token = request.POST.get("access_token", "").strip()

    if not account_name or not access_token:
        messages.error(request, "Account name and access token are required.")
        return redirect("fb_leads:fb_accounts")

    account = FacebookAccount.objects.create(
        account_name=account_name,
        access_token=access_token,
        connected_by=request.user,
        status="CONNECTED",
    )

    try:
        pages_count = sync_pages_for_account(account)
        messages.success(request, f"Connected Facebook Account '{account_name}' and imported {pages_count} page(s).")
        log_activity(
            user=request.user,
            action="Facebook Account Connected",
            description=f"Connected Facebook account '{account_name}' with {pages_count} pages.",
            object_type="FacebookAccount",
            object_id=account.id,
            request=request
        )
    except Exception as exc:
        messages.warning(request, f"Account saved, but could not retrieve pages immediately: {exc}")

    return redirect("fb_leads:fb_accounts")


@login_required
@require_POST
def fb_account_disconnect(request, account_id):
    """Disconnect and delete a Facebook Account and its associated Pages."""
    if not _can_manage(request.user):
        raise PermissionDenied("Only Admin and Sales Head can disconnect Facebook accounts.")

    from .models import FacebookAccount
    from .facebook import unsubscribe_page

    try:
        account = FacebookAccount.objects.get(id=account_id)
        # Attempt to unsubscribe all its pages
        for page in account.pages.all():
            try:
                unsubscribe_page(page.page_id)
            except Exception:
                pass
        name = account.account_name
        account.delete()
        messages.success(request, f"Disconnected Facebook Account '{name}'.")
        log_activity(
            user=request.user,
            action="Facebook Account Disconnected",
            description=f"Disconnected Facebook account '{name}'.",
            object_type="FacebookAccount",
            request=request
        )
    except FacebookAccount.DoesNotExist:
        messages.error(request, "Facebook Account not found.")

    return redirect("fb_leads:fb_accounts")


@login_required
@require_POST
def fb_page_update_branch(request, page_id):
    """Update default CRM branch for a Facebook Page."""
    if not _can_manage(request.user):
        raise PermissionDenied("Only Admin and Sales Head can configure branch routing.")

    from .models import FacebookPage
    from branches.models import Branch

    page = FacebookPage.objects.filter(id=page_id).first()
    if not page:
        messages.error(request, "Facebook Page not found.")
        return redirect("fb_leads:fb_accounts")

    branch_id = request.POST.get("branch_id")
    if branch_id:
        branch = Branch.objects.filter(id=branch_id).first()
        page.branch = branch
    else:
        page.branch = None
    page.save(update_fields=["branch"])

    messages.success(request, f"Updated branch assignment for '{page.page_name}'.")
    return redirect("fb_leads:fb_accounts")


@login_required
@require_POST
def fb_page_toggle_webhook(request, page_id):
    """Subscribe or unsubscribe a Facebook Page to/from webhooks."""
    if not _can_manage(request.user):
        raise PermissionDenied("Only Admin and Sales Head can configure webhooks.")

    from .models import FacebookPage
    from .facebook import subscribe_page, unsubscribe_page

    page = FacebookPage.objects.filter(id=page_id).first()
    if not page:
        messages.error(request, "Facebook Page not found.")
        return redirect("fb_leads:fb_accounts")

    try:
        if page.webhook_subscribed:
            unsubscribe_page(page.page_id)
            messages.success(request, f"Unsubscribed webhook for '{page.page_name}'.")
        else:
            subscribe_page(page.page_id)
            messages.success(request, f"Subscribed webhook for '{page.page_name}'.")
    except Exception as exc:
        messages.error(request, f"Webhook configuration error: {exc}")

    return redirect("fb_leads:fb_accounts")


@login_required
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

    try:
        n = trigger_immediate_page_sync(page.page_id)
        page.refresh_from_db()
        msg = f"Sync complete for '{page.page_name}': {n} new lead(s) imported."
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
def fb_page_toggle_autosync(request, page_id):
    """Enable or disable periodic background auto-sync for a Facebook Page."""
    from datetime import timedelta
    from django.utils import timezone
    from django.http import JsonResponse
    from .models import FacebookPage
    from .scheduler import ensure_scheduler_running

    if not _can_manage(request.user):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
        raise PermissionDenied("Only Admin and Sales Head can toggle auto-sync.")

    ensure_scheduler_running()

    page = FacebookPage.objects.filter(id=page_id).first()
    if not page:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Facebook Page not found"}, status=404)
        messages.error(request, "Facebook Page not found.")
        return redirect("fb_leads:fb_accounts")

    page.auto_sync_enabled = not page.auto_sync_enabled
    if page.auto_sync_enabled:
        interval = page.sync_interval_minutes or 3
        page.next_sync_at = timezone.now() + timedelta(minutes=interval)
        page.last_sync_status = f"Auto-sync enabled (every {interval}m)"
    else:
        page.next_sync_at = None
        page.last_sync_status = "Auto-sync paused"

    page.save(update_fields=["auto_sync_enabled", "next_sync_at", "last_sync_status"])

    status_text = "enabled" if page.auto_sync_enabled else "paused"
    msg = f"Auto-sync {status_text} for '{page.page_name}'."

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "auto_sync_enabled": page.auto_sync_enabled,
            "sync_interval_minutes": page.sync_interval_minutes,
            "last_sync_status": page.last_sync_status,
            "next_sync_at": page.next_sync_at.strftime("%H:%M") if page.next_sync_at else "Paused",
            "message": msg,
        })

    messages.success(request, msg)
    return redirect("fb_leads:fb_accounts")


@login_required
@require_POST
def fb_page_update_interval(request, page_id):
    """Update auto-sync frequency (minutes) for a Facebook Page."""
    from datetime import timedelta
    from django.utils import timezone
    from django.http import JsonResponse
    from .models import FacebookPage
    from .scheduler import ensure_scheduler_running

    if not _can_manage(request.user):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
        raise PermissionDenied("Only Admin and Sales Head can change auto-sync interval.")

    ensure_scheduler_running()

    page = FacebookPage.objects.filter(id=page_id).first()
    if not page:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Facebook Page not found"}, status=404)
        messages.error(request, "Facebook Page not found.")
        return redirect("fb_leads:fb_accounts")

    raw_val = request.POST.get("interval", "3")
    try:
        interval = int(raw_val)
        if interval not in [1, 3, 5, 10, 15, 30, 60]:
            interval = 3
    except (ValueError, TypeError):
        interval = 3

    page.sync_interval_minutes = interval
    if page.auto_sync_enabled:
        page.next_sync_at = timezone.now() + timedelta(minutes=interval)
        page.last_sync_status = f"Interval set to {interval}m"

    page.save(update_fields=["sync_interval_minutes", "next_sync_at", "last_sync_status"])

    msg = f"Updated sync interval to {interval} minute(s) for '{page.page_name}'."
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "sync_interval_minutes": page.sync_interval_minutes,
            "last_sync_status": page.last_sync_status,
            "next_sync_at": page.next_sync_at.strftime("%H:%M") if page.next_sync_at else "Paused",
            "message": msg,
        })

    messages.success(request, msg)
    return redirect("fb_leads:fb_accounts")


@login_required
def api_autosync_status(request):
    """
    Heartbeat and status endpoint for live dashboard updates.
    Returns status of all connected pages and triggers cycle if any is due.
    """
    from django.http import JsonResponse
    from django.utils import timezone
    from .models import FacebookPage
    from .scheduler import ensure_scheduler_running, run_auto_sync_cycle

    if not _can_manage(request.user):
        return JsonResponse({"success": False, "error": "Forbidden"}, status=403)

    ensure_scheduler_running()
    # Execute a cycle check (handles edge cases where thread was idle)
    try:
        run_auto_sync_cycle()
    except Exception as exc:
        log.warning("Heartbeat sync cycle check warning: %s", exc)

    now = timezone.now()
    pages_data = []
    for p in FacebookPage.objects.filter(status="CONNECTED"):
        seconds_left = None
        if p.auto_sync_enabled and p.next_sync_at:
            delta = (p.next_sync_at - now).total_seconds()
            seconds_left = max(0, int(delta))

        pages_data.append({
            "id": p.id,
            "page_id": p.page_id,
            "page_name": p.page_name,
            "auto_sync_enabled": p.auto_sync_enabled,
            "sync_interval_minutes": p.sync_interval_minutes,
            "last_sync_at": p.last_sync_at.strftime("%d %b, %H:%M") if p.last_sync_at else "Never synced",
            "last_sync_status": p.last_sync_status,
            "last_error": p.last_error,
            "next_sync_at": p.next_sync_at.strftime("%H:%M") if p.next_sync_at else "—",
            "seconds_left": seconds_left,
        })

    return JsonResponse({
        "success": True,
        "pages": pages_data,
        "server_time": now.strftime("%H:%M:%S"),
    })


