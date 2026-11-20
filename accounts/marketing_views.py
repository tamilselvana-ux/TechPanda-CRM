import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator

from accounts.models import User, UserRole
from accounts.permissions import admin_required, can_manage_user
from branches.models import Branch
from activities.utils import log_activity

logger = logging.getLogger(__name__)


@admin_required
def admin_marketing_users_list(request):
    """
    Administrator view listing all Marketing Team users.
    Provides search, active/inactive status filter, KPI counters, and management actions.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    page_size = request.GET.get('page_size', '15').strip()

    marketing_users = User.objects.filter(role=UserRole.MARKETING).order_by('-date_joined')

    if query:
        marketing_users = marketing_users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )

    if status_filter == 'active':
        marketing_users = marketing_users.filter(is_active=True)
    elif status_filter == 'inactive':
        marketing_users = marketing_users.filter(is_active=False)

    total_marketing = User.objects.filter(role=UserRole.MARKETING).count()
    active_marketing = User.objects.filter(role=UserRole.MARKETING, is_active=True).count()
    inactive_marketing = User.objects.filter(role=UserRole.MARKETING, is_active=False).count()

    try:
        page_size_int = int(page_size)
    except (ValueError, TypeError):
        page_size_int = 15

    paginator = Paginator(marketing_users, page_size_int)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'marketing_users': page_obj,
        'page_obj': page_obj,
        'total_marketing': total_marketing,
        'active_marketing': active_marketing,
        'inactive_marketing': inactive_marketing,
        'search_query': query,
        'selected_status': status_filter,
        'page_size': page_size_int,
        'portal_title': 'Marketing Team Staff Management',
    }
    return render(request, 'admin/marketing_users_list.html', context)


@admin_required
@require_POST
def admin_marketing_user_toggle_status(request, pk):
    """
    Toggles is_active status of a Marketing Team member.
    """
    target_user = get_object_or_404(User, pk=pk, role=UserRole.MARKETING)
    if not can_manage_user(request.user, target_user):
        messages.error(request, "Permission denied.")
        return redirect('admin_marketing_users_list')

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])

    status_str = "activated" if target_user.is_active else "deactivated"
    messages.success(request, f"Marketing member {target_user.get_full_name() or target_user.username} has been {status_str}.")
    log_activity(request.user, 'UPDATED', f"Changed Marketing user {target_user.username} active status to {target_user.is_active}")
    return redirect('admin_marketing_users_list')
