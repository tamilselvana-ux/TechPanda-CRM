import logging
from io import StringIO
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.management import call_command
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from leads.models import LeadStatus
from .models import TeleCRMAction, TeleCRMLead, TeleCRMStatusMap, TeleCRMSyncRun, TeleCRMUser

logger = logging.getLogger("telecrm_sync")
User = get_user_model()


def is_admin_user(user) -> bool:
    """Restricts access to superadmins and administrators."""
    return bool(user.is_authenticated and (user.is_superuser or user.role in ("SUPERADMIN", "ADMIN")))


@login_required
@user_passes_test(is_admin_user)
def telecrm_sync_dashboard(request):
    """
    Administrative management and diagnostic dashboard for TeleCRM Integration.
    Displays health indicators, last run status, execution history, unmapped metadata,
    and manual trigger controls.
    """
    # Automatically mark abandoned runs older than 30 minutes as FAILED
    from django.utils import timezone
    stale_cutoff = timezone.now() - timezone.timedelta(minutes=30)
    TeleCRMSyncRun.objects.filter(status="RUNNING", started_at__lt=stale_cutoff).update(
        status="FAILED",
        finished_at=timezone.now()
    )

    last_run = TeleCRMSyncRun.objects.order_by("-started_at").first()
    recent_runs = TeleCRMSyncRun.objects.order_by("-started_at")[:15]

    total_leads_mirrored = TeleCRMLead.objects.count()
    total_actions_mirrored = TeleCRMAction.objects.count()

    # Collect errors from recent runs
    recent_errors = []
    for r in recent_runs:
        if r.errors:
            for err in r.errors:
                recent_errors.append({
                    "run_id": r.id,
                    "kind": r.kind,
                    "timestamp": err.get("timestamp") or r.started_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "detail": err.get("detail") or err.get("error") or str(err)
                })

    status_mappings = TeleCRMStatusMap.objects.all().order_by("telecrm_status_name")
    unmapped_statuses_count = status_mappings.filter(crm_status=LeadStatus.NEW).count()

    telecrm_users = TeleCRMUser.objects.all().select_related("crm_user").order_by("name", "email")
    unmapped_users = telecrm_users.filter(crm_user__isnull=True)

    all_crm_users = User.objects.filter(is_active=True).order_by("first_name", "username")

    context = {
        "last_run": last_run,
        "recent_runs": recent_runs,
        "total_leads_mirrored": total_leads_mirrored,
        "total_actions_mirrored": total_actions_mirrored,
        "recent_errors": recent_errors[:20],
        "status_mappings": status_mappings,
        "unmapped_statuses_count": unmapped_statuses_count,
        "telecrm_users": telecrm_users,
        "unmapped_users": unmapped_users,
        "all_crm_users": all_crm_users,
        "lead_status_choices": LeadStatus.choices,
        "sync_enabled": getattr(settings, "TELECRM_SYNC_ENABLED", False),
        "sync_interval_min": getattr(settings, "TELECRM_SYNC_INTERVAL_MIN", 5),
        "enterprise_id": getattr(settings, "TELECRM_ENTERPRISE_ID", "681848fb55c90e360f77494c"),
    }
    return render(request, "admin/telecrm_sync_dashboard.html", context)


@login_required
@user_passes_test(is_admin_user)
@require_POST
def telecrm_run_sync_now(request):
    """
    Manual trigger to execute telecrm_sync management command on demand.
    """
    out = StringIO()
    try:
        call_command("telecrm_sync", force=True, stdout=out)
        result_text = out.getvalue().strip()
        last_line = result_text.splitlines()[-1] if result_text else "Sync completed successfully."
        messages.success(request, f"Manual TeleCRM sync executed: {last_line}")
    except Exception as exc:
        logger.exception("Manual TeleCRM sync failed: %s", exc)
        messages.error(request, f"Manual TeleCRM sync failed: {exc}")

    return redirect("admin_telecrm_sync_dashboard")


@login_required
@user_passes_test(is_admin_user)
@require_POST
def telecrm_update_status_map(request):
    """
    Updates the target CRM LeadStatus for a TeleCRM pipeline status.
    """
    mapping_id = request.POST.get("mapping_id") or request.POST.get("map_id")
    target_status = request.POST.get("crm_status", "").strip()

    mapping = get_object_or_404(TeleCRMStatusMap, id=mapping_id)
    if target_status in dict(LeadStatus.choices):
        mapping.crm_status = target_status
        mapping.save(update_fields=["crm_status"])
        messages.success(request, f"Status mapping updated: {mapping.telecrm_status_name} -> {mapping.crm_status}")
    else:
        messages.error(request, f"Invalid target status selected: {target_status}")

    return redirect("admin_telecrm_sync_dashboard")


@login_required
@user_passes_test(is_admin_user)
@require_POST
def telecrm_update_user_map(request):
    """
    Updates or links a TeleCRM internal UID to a native CRM User account.
    """
    mapping_id = request.POST.get("mapping_id")
    user_id = request.POST.get("crm_user_id", "").strip()

    mapping = get_object_or_404(TeleCRMUser, id=mapping_id)
    if user_id:
        crm_user = get_object_or_404(User, id=user_id)
        mapping.crm_user = crm_user
        mapping.save(update_fields=["crm_user"])
        messages.success(request, f"User mapping updated: {mapping.name or mapping.email} -> {crm_user.username}")
    else:
        mapping.crm_user = None
        mapping.save(update_fields=["crm_user"])
        messages.info(request, f"User mapping cleared for {mapping.name or mapping.email}")

    return redirect("admin_telecrm_sync_dashboard")
