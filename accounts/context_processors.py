from followups.models import FollowUp, FollowUpStatus
from django.db.models import Q
from django.utils import timezone

def crm_context(request):
    context = {
        'APP_NAME': 'TechPanda CRM', 'COMPANY_NAME': 'TechPanda CRM',
        'is_admin': False,
        'is_manager': False,
        'is_branch_head': False,
        'is_branch_admin': False,
        'is_counselor': False,
        'is_telecaller': False,
        'is_receptionist': False,
        'is_accountant': False,
        'is_finance_head': False,
        'is_marketing': False,
        'user_role': '',
        'pending_followups_count': 0,
        'overdue_followups_count': 0,
        'unread_notifications_count': 0,
    }
    if request.user.is_authenticated:
        context['is_superadmin'] = request.user.is_superadmin_user
        context['is_admin'] = request.user.is_admin_user
        context['is_manager'] = request.user.is_sales_head_user
        context['is_branch_head'] = request.user.is_branch_head_user
        context['is_branch_admin'] = request.user.is_branch_admin_user
        context['is_counselor'] = request.user.is_counselor_user
        context['is_telecaller'] = request.user.is_telecaller_user
        context['is_receptionist'] = request.user.is_receptionist_user
        context['is_accountant'] = request.user.is_accountant_user
        context['is_finance_head'] = request.user.is_finance_head_user
        context['is_marketing'] = getattr(request.user, 'is_marketing_user', False)
        context['user_role'] = request.user.display_role

        if request.user.is_admin_user:
            from branches.models import Branch
            from branches.utils import get_admin_selected_branch
            from accounts.models import User, UserRole
            from django.db.models import Count

            context['admin_branches'] = Branch.objects.filter(status=Branch.Status.ACTIVE).order_by('name')
            selected_b = get_admin_selected_branch(request)
            context['selected_branch'] = selected_b

            staff_qs = User.objects.all()
            if selected_b:
                staff_qs = staff_qs.filter(Q(branch=selected_b) | Q(branch_access__branch=selected_b)).distinct()

            role_counts = dict(staff_qs.values_list('role').annotate(cnt=Count('id', distinct=True)))

            context['staff_counts'] = {
                'total': staff_qs.count(),
                'sales_heads': role_counts.get(UserRole.SALES_HEAD, 0),
                'branch_heads': role_counts.get(UserRole.BRANCH_HEAD, 0),
                'branch_admins': role_counts.get(UserRole.BRANCH_ADMIN, 0),
                'counselors': role_counts.get(UserRole.COUNSELOR, 0),
                'telecallers': role_counts.get(UserRole.TELECALLER, 0),
                'receptionists': role_counts.get(UserRole.RECEPTIONIST, 0),
                'accountants': role_counts.get(UserRole.ACCOUNTANT, 0),
                'marketing': role_counts.get(UserRole.MARKETING, 0),
            }

        # Scoped notification counters
        today = timezone.now().date()
        qs = FollowUp.objects.filter(status=FollowUpStatus.PENDING)
        if request.user.is_telecaller_user:
            qs = qs.filter(telecaller=request.user)
        elif request.user.is_sales_head_user:
            from accounts.permissions import get_accessible_branch_ids
            qs = qs.filter(
                Q(manager=request.user) | Q(telecaller__branch_id__in=get_accessible_branch_ids(request.user))
            )
        
        context['pending_followups_count'] = qs.count()
        context['overdue_followups_count'] = qs.filter(follow_up_date__lt=today).count()
        
        from activities.models import Notification
        context['unread_notifications_count'] = Notification.objects.filter(recipient=request.user, is_read=False).count()
        
    return context
