import logging
from django import forms
from django.core.exceptions import ValidationError
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


class MarketingUserEditForm(forms.ModelForm):
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.none(),
        required=False,
        empty_label="All Branches (Universal)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'branch', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, allowed_branches=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['branch'].queryset = allowed_branches if allowed_branches is not None else Branch.objects.filter(status='Active')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            raise ValidationError("Email is required.")
        exists_qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            exists_qs = exists_qs.exclude(pk=self.instance.pk)
        if exists_qs.exists():
            raise ValidationError("A user with this email address already exists.")
        return email


@admin_required
def admin_marketing_users_list(request):
    """
    Administrator view listing all Marketing Team users.
    Provides search, active/inactive status filter, branch filter, KPI counters, and management actions.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    branch_filter = request.GET.get('branch', '').strip()
    page_size = request.GET.get('page_size', '15').strip()

    marketing_users = User.objects.filter(role=UserRole.MARKETING).select_related('branch').order_by('-date_joined')

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

    if branch_filter and branch_filter.isdigit():
        marketing_users = marketing_users.filter(branch_id=int(branch_filter))

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
        'branches': Branch.objects.filter(status='Active').order_by('name'),
        'total_marketing': total_marketing,
        'active_marketing': active_marketing,
        'inactive_marketing': inactive_marketing,
        'search_query': query,
        'selected_status': status_filter,
        'selected_branch': branch_filter,
        'page_size': page_size_int,
        'portal_title': 'Marketing Team Staff Management',
    }
    return render(request, 'admin/marketing_users_list.html', context)


@admin_required
def admin_marketing_user_detail(request, pk):
    """
    Administrator profile & oversight view for a Marketing user.
    Displays profile information, universal access permissions, total accessible leads, and recent activity logs.
    """
    from leads.models import Lead
    from activities.models import Activity

    marketing_user = get_object_or_404(User.objects.select_related('branch'), pk=pk, role=UserRole.MARKETING)
    total_leads_count = Lead.objects.count()
    active_leads_count = Lead.objects.exclude(status__in=['Lost', 'Converted']).count()
    recent_activities = Activity.objects.filter(user=marketing_user).order_by('-timestamp')[:15]

    context = {
        'target_user': marketing_user,
        'total_leads_count': total_leads_count,
        'active_leads_count': active_leads_count,
        'recent_activities': recent_activities,
        'portal_title': f"Marketing Profile - {marketing_user.get_full_name() or marketing_user.username}",
    }
    return render(request, 'admin/marketing_user_detail.html', context)


@admin_required
def admin_marketing_user_edit(request, pk):
    """
    Administrator view to edit profile details for a Marketing user.
    """
    marketing_user = get_object_or_404(User, pk=pk, role=UserRole.MARKETING)
    if not can_manage_user(request.user, marketing_user):
        messages.error(request, "Permission denied.")
        return redirect('admin_marketing_users_list')

    allowed_branches = Branch.objects.filter(status='Active')
    if request.method == 'POST':
        form = MarketingUserEditForm(request.POST, instance=marketing_user, allowed_branches=allowed_branches)
        if form.is_valid():
            form.save()
            log_activity(
                user=request.user,
                action="Marketing User Updated",
                description=f"Admin updated profile details for Marketing user '{marketing_user.username}'.",
                object_type="User",
                object_id=str(marketing_user.pk),
                request=request
            )
            messages.success(request, f"Marketing member '{marketing_user.get_full_name() or marketing_user.username}' was updated successfully.")
            return redirect('admin_marketing_user_detail', pk=marketing_user.pk)
    else:
        form = MarketingUserEditForm(instance=marketing_user, allowed_branches=allowed_branches)

    return render(request, 'admin/marketing_user_edit.html', {
        'form': form,
        'target_user': marketing_user,
        'portal_title': f"Edit Marketing Member - {marketing_user.username}",
    })


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
