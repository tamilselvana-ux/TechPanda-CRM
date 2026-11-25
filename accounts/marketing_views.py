import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.db.models import Q

from accounts.models import User, UserRole
from accounts.permissions import admin_required, can_manage_user
from branches.models import Branch
from activities.utils import log_activity

logger = logging.getLogger(__name__)


@login_required
def marketing_dashboard(request):
    """
    Dedicated workspace dashboard for Marketing team members (and Admins).
    Surfaces key acquisition metrics: Facebook leads, WhatsApp campaigns, automations,
    and recent campaign performance.
    """
    user = request.user
    if not (user.is_superuser or user.role in (UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.MARKETING)):
        raise PermissionDenied("Access denied: You do not have permission to view the Marketing Dashboard.")

    from django.utils import timezone
    from leads.models import Lead, LeadStatus
    from fb_leads.models import FacebookLead, FacebookPage
    from chat.models import WhatsAppCampaign, AutomationFlow

    today = timezone.localdate()

    # Exact CRM lead counts matching SuperAdmin All Leads
    total_leads = Lead.objects.count()
    today_leads = Lead.objects.filter(created_at__date=today).count()
    meta_leads_count = Lead.objects.filter(
        Q(channel__name__icontains='meta') | Q(channel__name__icontains='facebook') |
        Q(source__icontains='meta') | Q(source__icontains='facebook')
    ).count()
    today_meta_leads = Lead.objects.filter(
        Q(channel__name__icontains='meta') | Q(channel__name__icontains='facebook') |
        Q(source__icontains='meta') | Q(source__icontains='facebook'),
        created_at__date=today
    ).count()

    total_fb_leads = FacebookLead.objects.count()
    connected_pages_count = FacebookPage.objects.filter(status='CONNECTED').count()

    total_campaigns = WhatsAppCampaign.objects.count()
    active_campaigns = WhatsAppCampaign.objects.filter(status__in=['SCHEDULED', 'RUNNING', 'SENDING']).count()

    active_flows = AutomationFlow.objects.filter(is_active=True).count()

    recent_fb_leads = FacebookLead.objects.select_related('lead', 'fb_page').order_by('-received_at')[:10]

    context = {
        'total_leads': total_leads,
        'today_leads': today_leads,
        'meta_leads_count': meta_leads_count,
        'today_meta_leads': today_meta_leads,
        'total_fb_leads': total_fb_leads,
        'connected_pages_count': connected_pages_count,
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'active_flows': active_flows,
        'recent_fb_leads': recent_fb_leads,
        'today': today,
        'portal_title': 'Marketing Portal',
    }
    return render(request, 'marketing/dashboard.html', context)


@admin_required
def admin_marketing_users_list(request):
    """
    Administrator view listing all Marketing team members across branches.
    Provides branch filter, search, status filter, and action buttons.
    """
    query = request.GET.get('q', '').strip()
    branch_id = request.GET.get('branch', '').strip()
    status_filter = request.GET.get('status', '').strip()

    marketing_users = User.objects.filter(role=UserRole.MARKETING).select_related('branch').order_by('-date_joined')

    if query:
        marketing_users = marketing_users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )

    if branch_id and branch_id.isdigit():
        marketing_users = marketing_users.filter(branch_id=int(branch_id))

    if status_filter == 'active':
        marketing_users = marketing_users.filter(is_active=True)
    elif status_filter == 'inactive':
        marketing_users = marketing_users.filter(is_active=False)

    branches = Branch.objects.filter(status='Active')

    total_marketing = marketing_users.count()
    active_marketing = marketing_users.filter(is_active=True).count()
    inactive_marketing = marketing_users.filter(is_active=False).count()

    context = {
        'marketing_users': marketing_users,
        'branches': branches,
        'selected_branch': branch_id,
        'selected_status': status_filter,
        'search_query': query,
        'total_marketing': total_marketing,
        'active_marketing': active_marketing,
        'inactive_marketing': inactive_marketing,
        'portal_title': 'Marketing Team Management',
    }
    return render(request, 'admin/marketing_list.html', context)


@admin_required
@require_POST
def admin_marketing_toggle_status(request, pk):
    """
    Activates or deactivates a Marketing team user account.
    """
    target_user = get_object_or_404(User, pk=pk, role=UserRole.MARKETING)

    if not can_manage_user(request.user, target_user):
        messages.error(request, "Permission denied.")
        return redirect('admin_marketing_users_list')

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])

    status_str = "activated" if target_user.is_active else "deactivated"
    log_activity(
        user=request.user,
        action=f"Marketing Member {status_str.title()}",
        description=f"Administrator {request.user.username} {status_str} marketing member '{target_user.username}'.",
        object_type="User",
        object_id=str(target_user.pk),
        request=request
    )
    messages.success(request, f"Marketing member '{target_user.username}' {status_str} successfully.")
    return redirect('admin_marketing_users_list')
