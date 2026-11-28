import logging
from io import StringIO
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from activities.models import Activity
from leads.models import LeadStatus, LeadStatusHistory
from .models import SyncConflict, TeleCRMAction, TeleCRMLead, TeleCRMStatusMap, TeleCRMSyncRun, TeleCRMUser

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

    # Collect errors from recent runs (always include latest/failed runs even if errors JSON is empty)
    recent_errors = []
    for r in recent_runs:
        if r.errors:
            for err in r.errors:
                if isinstance(err, dict):
                    ts = err.get("timestamp") or (r.finished_at or r.started_at).strftime("%Y-%m-%d %H:%M:%S")
                    detail = err.get("detail") or err.get("error") or str(err)
                else:
                    ts = (r.finished_at or r.started_at).strftime("%Y-%m-%d %H:%M:%S")
                    detail = str(err)
                recent_errors.append({
                    "run_id": r.id,
                    "kind": r.kind,
                    "timestamp": ts,
                    "detail": detail,
                })
        elif r.status == "FAILED":
            recent_errors.append({
                "run_id": r.id,
                "kind": r.kind,
                "timestamp": (r.finished_at or r.started_at).strftime("%Y-%m-%d %H:%M:%S"),
                "detail": "Run marked FAILED without a recorded exception (process interrupted/terminated or timed out).",
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


def can_view_sync_conflicts(user) -> bool:
    """Allows Superadmin, Admin, Sales Head, and Branch Head."""
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.role in ("SUPERADMIN", "ADMIN", "SALES_HEAD", "BRANCH_HEAD"))
    )


def _conflict_queryset_for_user(user):
    qs = SyncConflict.objects.select_related("lead", "lead__branch", "telecrm_lead", "resolved_by")
    if user.is_superuser or user.role in ("SUPERADMIN", "ADMIN", "SALES_HEAD"):
        return qs
    if user.role == "BRANCH_HEAD":
        if user.branch_id:
            return qs.filter(lead__branch_id=user.branch_id)
        return qs.none()
    return qs.none()


@login_required
def telecrm_sync_conflicts(request):
    """
    Lists TeleCRM <-> CRM status conflicts for review and one-click resolution.
    Scoped to Admin/Sales Head (all branches) and Branch Head (own branch only).
    """
    if not can_view_sync_conflicts(request.user):
        raise PermissionDenied("You do not have permission to view Sync Conflicts.")

    status_filter = request.GET.get("status", "OPEN").upper()
    base_qs = _conflict_queryset_for_user(request.user)

    open_count = base_qs.filter(status=SyncConflict.STATUS_OPEN).count()
    resolved_count = base_qs.exclude(status=SyncConflict.STATUS_OPEN).count()

    if status_filter in (SyncConflict.STATUS_OPEN, SyncConflict.STATUS_KEPT_CRM, SyncConflict.STATUS_USED_TELECRM):
        conflicts_qs = base_qs.filter(status=status_filter)
    else:
        conflicts_qs = base_qs
        status_filter = "ALL"

    context = {
        "conflicts": conflicts_qs[:200],
        "status_filter": status_filter,
        "open_count": open_count,
        "resolved_count": resolved_count,
        "is_branch_scoped": request.user.role == "BRANCH_HEAD" and not request.user.is_superuser,
    }
    return render(request, "admin/telecrm_conflicts.html", context)


@login_required
@require_POST
def telecrm_resolve_conflict(request, conflict_id):
    """
    Resolves a SyncConflict with either 'keep_crm' or 'use_telecrm',
    updates Lead.status, writes LeadStatusHistory, and logs an Activity audit entry.
    """
    if not can_view_sync_conflicts(request.user):
        raise PermissionDenied("You do not have permission to resolve Sync Conflicts.")

    conflict = get_object_or_404(_conflict_queryset_for_user(request.user), id=conflict_id)
    decision = (request.POST.get("decision") or "").strip().lower()
    if decision not in ("keep_crm", "use_telecrm"):
        messages.error(request, "Invalid conflict resolution decision.")
        return redirect("telecrm_sync_conflicts")

    with transaction.atomic():
        lead = conflict.lead
        prev_status = lead.status
        if decision == "keep_crm":
            chosen_status = conflict.crm_status
            new_state = SyncConflict.STATUS_KEPT_CRM
            source_tag = "CRM"
            action_label = "Keep CRM"
        else:
            chosen_status = conflict.telecrm_status
            new_state = SyncConflict.STATUS_USED_TELECRM
            source_tag = "TeleCRM"
            action_label = "Use TeleCRM"

        if lead.status != chosen_status:
            lead.status = chosen_status
            lead.save(update_fields=["status", "updated_at"])
            LeadStatusHistory.objects.create(
                lead=lead,
                old_status=prev_status,
                new_status=chosen_status,
                changed_by=request.user,
                remarks=f"[{source_tag}] Sync conflict #{conflict.id} resolved ({action_label})",
            )

        if conflict.telecrm_lead:
            conflict.telecrm_lead.last_synced_status = chosen_status
            conflict.telecrm_lead.save(update_fields=["last_synced_status"])

        conflict.status = new_state
        conflict.resolved_by = request.user
        conflict.resolved_at = timezone.now()
        conflict.notes = f"Resolved by {request.user.username} via {action_label} (prev={prev_status} -> {chosen_status})"
        conflict.save(update_fields=["status", "resolved_by", "resolved_at", "notes"])

        Activity.objects.create(
            user=request.user,
            action="TeleCRM Conflict Resolved",
            object_type="Lead",
            object_id=str(lead.id),
            description=(
                f"Resolved SyncConflict #{conflict.id} for {lead.name} ({lead.phone}): "
                f"{action_label} -> {chosen_status} (CRM={conflict.crm_status}, TeleCRM={conflict.telecrm_status})"
            ),
        )

    messages.success(request, f"Conflict #{conflict.id} resolved ({action_label}): Lead #{lead.id} set to {chosen_status}.")
    return redirect("telecrm_sync_conflicts")
