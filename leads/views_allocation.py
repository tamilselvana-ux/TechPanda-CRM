import re
import csv
import io
import json
import logging
import openpyxl
from datetime import datetime, timedelta, time
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from accounts.models import User, UserRole
from accounts.permissions import (
    admin_required, lead_allocation_setup_required, sales_head_required, telecaller_required, branch_head_required, counselor_required,
    can_access_lead, can_view_lead, get_accessible_branch_ids,
)
from .handoff_service import change_lead_status
from branches.models import Branch
from lead_channels.models import Channel
from products.models import Product
from followups.models import FollowUp, FollowUpStatus
from calls.models import CallHistory, CallStatus, CallOutcome
from activities.models import Activity
from activities.utils import log_activity
from branches.utils import get_admin_selected_branch
from .models import (
    Lead, LeadStatus, LeadCategory, VisitorStatus, LeadOwnerType, LeadImportHistory,
    GoogleFormConnection, LeadSetupConfig, TelecallerLeadSetup,
    DuplicateLeadRecord, AssignmentMethod
)
from .forms import (
    AdminLeadForm, ManagerLeadForm, TelecallerLeadForm,
    ManagerLeadCreateForm, TelecallerLeadCreateForm, LeadImportForm
)
from .services import import_leads_file
from .duplicates import (
    find_duplicate_lead,
    handle_incoming_lead_duplicate,
    detect_all_duplicate_groups,
    keep_single_lead_for_group,
    process_incoming_lead_with_10day_rule,
    mask_phone,
    process_spreadsheet_row_duplicate_rules,
)
from .assignment import (
    assign_lead_to_branch_telecaller,
    assign_lead_automatically,
    assign_new_lead,
    apply_branch_lead_distribution,
    retry_pending_assignments
)

logger = logging.getLogger('crm')


@login_required

def admin_lead_queues(request):

    """

    Management view for the 4 distinct lead assignment queues:

    - Unassigned

    - Untouched

    - Unanswered

    - Unattended

    Supports filtering by branch, searching, pagination, and bulk assignment via single or round-robin strategies.

    """

    user = request.user

    if not (user.is_admin_user or user.role in (UserRole.SALES_HEAD, UserRole.BRANCH_HEAD)):

        raise PermissionDenied("You do not have permission to access lead assignment queues.")



    current_queue = request.GET.get('queue', 'unassigned').lower().strip()

    if current_queue not in ('unassigned', 'untouched', 'unanswered', 'unattended'):

        current_queue = 'unassigned'



    branch_filter = request.GET.get('branch', '').strip()

    search_query = request.GET.get('search', '').strip()



    from .bulk_assignment_service import get_queue_queryset, get_queue_counts

    queue_counts = get_queue_counts(branch=branch_filter or None, user=user)

    current_queue_count = queue_counts.get(current_queue, 0)



    leads_qs = get_queue_queryset(current_queue, branch=branch_filter or None, user=user)



    if search_query:

        leads_qs = leads_qs.filter(

            Q(name__icontains=search_query) |

            Q(phone__icontains=search_query) |

            Q(notes__icontains=search_query)

        )



    from .utils import get_validated_page_size, ALLOWED_PAGE_SIZES

    page_size = get_validated_page_size(request, default=20)

    paginator = Paginator(leads_qs, page_size)

    page_obj = paginator.get_page(request.GET.get('page'))



    if user.is_admin_user:

        branches = Branch.objects.filter(status='Active')

    else:

        from accounts.permissions import get_accessible_branch_ids

        branches = Branch.objects.filter(id__in=get_accessible_branch_ids(user), status='Active')



    tc_qs = User.objects.filter(role=UserRole.TELECALLER, is_active=True).select_related('branch')

    if branch_filter:

        tc_qs = tc_qs.filter(branch_id=branch_filter)

    elif not user.is_admin_user and user.branch_id:

        tc_qs = tc_qs.filter(branch_id=user.branch_id)

    telecallers = list(tc_qs.order_by('first_name', 'username'))



    # Modal multi-selection options: all active accessible branches and telecallers

    if user.is_admin_user:

        modal_branches = list(Branch.objects.filter(status='Active').order_by('name'))

        modal_tc_qs = User.objects.filter(role=UserRole.TELECALLER, is_active=True).select_related('branch')

    else:

        from accounts.permissions import get_accessible_branch_ids

        accessible_branch_ids = get_accessible_branch_ids(user)

        modal_branches = list(Branch.objects.filter(id__in=accessible_branch_ids, status='Active').order_by('name'))

        modal_tc_qs = User.objects.filter(role=UserRole.TELECALLER, is_active=True, branch_id__in=accessible_branch_ids).select_related('branch')



    telecallers_data = [

        {

            'id': tc.id,

            'name': tc.get_full_name() or tc.username,

            'username': tc.username,

            'branch_id': tc.branch_id,

            'branch_name': tc.branch.name if tc.branch else 'No Branch'

        }

        for tc in modal_tc_qs.order_by('first_name', 'username')

    ]



    return render(request, 'admin/lead_queues.html', {

        'page_obj': page_obj,

        'current_queue': current_queue,

        'queue_counts': queue_counts,

        'current_queue_count': current_queue_count,

        'branches': branches,

        'telecallers': telecallers,

        'modal_branches': modal_branches,

        'telecallers_data_json': json.dumps(telecallers_data),

        'branch_filter': branch_filter,

        'search_query': search_query,

    })


@login_required

@require_POST

def api_bulk_assign_leads(request):

    """

    API endpoint for executing atomic bulk lead assignment on queues.

    Supports single telecaller or multi-branch round-robin distribution with branch compatibility.

    """

    user = request.user

    if not (user.is_admin_user or user.role in (UserRole.SALES_HEAD, UserRole.BRANCH_HEAD)):

        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)



    try:

        if request.content_type == 'application/json':

            data = json.loads(request.body)

        else:

            data = request.POST



        queue_type = data.get('queue_type', 'unassigned')

        strategy = data.get('strategy', 'round_robin')

        target_telecaller_id = data.get('target_telecaller_id')

        target_branch_id = data.get('target_branch_id')

        branch_ids = data.get('branch_ids')

        telecaller_ids = data.get('telecaller_ids')

        reason = data.get('reason', '')

        lead_ids = data.get('lead_ids')

        target_role = data.get('target_role', 'TELECALLER')

        limit = data.get('limit')



        from .bulk_assignment_service import execute_bulk_assignment

        result = execute_bulk_assignment(

            queue_type=queue_type,

            lead_ids=lead_ids,

            strategy=strategy,

            target_role=target_role,

            target_telecaller_id=target_telecaller_id,

            target_branch_id=target_branch_id,

            branch_ids=branch_ids,

            telecaller_ids=telecaller_ids,

            reason=reason,

            assigned_by=user,

            limit=limit

        )



        return JsonResponse(result)

    except Exception as e:

        logger.exception("api_bulk_assign_leads failed: %s", e)

        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required

@require_POST

def api_bulk_assign_preview(request):

    """

    API endpoint returning real-time assignment preview stats:

    - total eligible leads

    - selected branch count

    - selected telecaller count

    - estimated leads per telecaller

    - branch compatibility warnings

    """

    user = request.user

    if not (user.is_admin_user or user.role in (UserRole.SALES_HEAD, UserRole.BRANCH_HEAD)):

        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)



    try:

        if request.content_type == 'application/json':

            data = json.loads(request.body)

        else:

            data = request.POST



        queue_type = data.get('queue_type', 'unassigned')

        branch_ids = data.get('branch_ids')

        telecaller_ids = data.get('telecaller_ids')

        lead_ids = data.get('lead_ids')



        from .bulk_assignment_service import get_bulk_assignment_preview

        preview = get_bulk_assignment_preview(

            queue_type=queue_type,

            branch_ids=branch_ids,

            telecaller_ids=telecaller_ids,

            lead_ids=lead_ids,

            user=user

        )

        return JsonResponse({'success': True, 'preview': preview})

    except Exception as e:

        logger.exception("api_bulk_assign_preview failed: %s", e)

        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required

@require_POST

def api_reassign_lead_to_counselor(request, pk):

    """

    Reassigns a lead from a telecaller (or unassigned/counselor) to a target counselor.

    Ensures branch compatibility and permission validation via can_reassign_lead.

    Writes audit record to LeadAssignmentHistory and Activity log.

    Supports both JSON and POST form submissions.

    """

    lead = get_object_or_404(Lead, pk=pk)



    if request.content_type == 'application/json':

        try:

            data = json.loads(request.body)

        except Exception:

            data = {}

    else:

        data = request.POST



    counselor_id = data.get('counselor_id') or data.get('counselor')

    reason = (data.get('reason') or 'Reassigned to Counselor').strip()



    if not counselor_id:

        return JsonResponse({'success': False, 'error': 'Counselor ID is required.'}, status=400)



    target_counselor = get_object_or_404(User, pk=counselor_id, role=UserRole.COUNSELOR)



    if not target_counselor.is_active:

        return JsonResponse({'success': False, 'error': 'Target counselor is inactive.'}, status=400)



    from accounts.permissions import can_reassign_lead

    if not can_reassign_lead(request.user, lead, target_counselor):

        return JsonResponse({

            'success': False,

            'error': f"You do not have permission to reassign this lead to Counselor '{target_counselor.username}'."

        }, status=403)



    from .handoff_service import handoff_to_counselor

    with transaction.atomic():

        handoff_to_counselor(lead, counselor=target_counselor, assigned_by=request.user, reason=reason)

        log_activity(

            user=request.user,

            action="Lead Reassigned to Counselor",

            description=f"Lead #{lead.id} ({lead.name}) reassigned to Counselor '{target_counselor.username}'. Reason: {reason}",

            object_type="Lead",

            object_id=lead.id,

            request=request

        )



    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':

        return JsonResponse({

            'success': True,

            'lead_id': lead.id,

            'counselor_id': target_counselor.id,

            'counselor_name': target_counselor.get_full_name() or target_counselor.username,

            'message': f"Lead successfully reassigned to Counselor '{target_counselor.username}'."

        })



    messages.success(request, f"Lead #{lead.id} successfully reassigned to Counselor '{target_counselor.username}'.")

    next_url = data.get('next') or request.META.get('HTTP_REFERER')

    if next_url:

        return redirect(next_url)

    return redirect('admin_lead_detail', pk=lead.pk)


@login_required

@require_POST

def api_resolve_lead_selection(request):

    """

    Validates selected leads or filter parameters before campaign creation.

    Returns counts for total, eligible, skipped, invalid phones, and opt-outs.

    """

    try:

        try:

            data = json.loads(request.body)

        except Exception:

            data = request.POST



        lead_ids = data.get('lead_ids', [])

        filter_params = data.get('filters', {})

        user = request.user



        qs = Lead.objects.all().select_related('branch', 'assigned_telecaller')



        # Enforce role visibility

        if not (getattr(user, 'is_admin_user', False) or user.is_superuser or user.role == 'ADMIN'):

            if user.role == 'SALES_HEAD':

                from branches.models import SalesHeadBranchAccess

                branches = SalesHeadBranchAccess.objects.filter(sales_head=user).values_list('branch_id', flat=True)

                qs = qs.filter(branch_id__in=list(branches))

            elif user.role == 'BRANCH_HEAD':

                qs = qs.filter(branch=user.branch)

            elif user.role == 'TELECALLER':

                qs = qs.filter(assigned_telecaller=user)

            elif user.role == 'COUNSELOR':

                qs = qs.filter(assigned_counselor=user)



        if lead_ids:

            qs = qs.filter(id__in=lead_ids)

        elif filter_params:

            if filter_params.get('search'):

                q = filter_params['search']

                qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q))

            if filter_params.get('branch'):

                qs = qs.filter(branch_id=filter_params['branch'])

            if filter_params.get('status'):

                qs = qs.filter(status=filter_params['status'])

            if filter_params.get('telecaller'):

                qs = qs.filter(assigned_telecaller_id=filter_params['telecaller'])



        from chat.campaign_service import normalize_phone_number



        total = 0

        eligible = 0

        invalid_phone = 0

        opted_out = 0



        for ld in qs.iterator(chunk_size=500):

            total += 1

            digits, is_valid, _ = normalize_phone_number(ld.phone)

            if not is_valid:

                invalid_phone += 1

                continue

            if getattr(ld, 'whatsapp_opt_out', False) or not getattr(ld, 'whatsapp_consent_given', True):

                opted_out += 1

                continue

            eligible += 1



        skipped = invalid_phone + opted_out

        return JsonResponse({

            'success': True,

            'total_selected': total,

            'eligible_count': eligible,

            'skipped_count': skipped,

            'invalid_phone_count': invalid_phone,

            'opted_out_count': opted_out,

        })

    except Exception as e:

        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required

@require_POST

def api_bulk_action(request):

    """

    Safe atomic bulk operations endpoint for leads.

    Supports bulk status updates and reassignment with individual permission verification

    via can_access_lead(), change_lead_status(), and reassign_lead().

    """

    try:

        try:

            data = json.loads(request.body)

        except Exception:

            data = request.POST



        action = data.get('action')

        lead_ids = data.get('lead_ids', [])

        if not lead_ids or not isinstance(lead_ids, list):

            return JsonResponse({'success': False, 'error': 'No leads selected'}, status=400)



        if len(lead_ids) > 100:

            return JsonResponse({'success': False, 'error': 'Maximum 100 leads per bulk operation'}, status=400)



        user = request.user

        leads = Lead.objects.filter(id__in=lead_ids)



        updated_count = 0

        errors = []



        if action == 'status_update':

            new_status = data.get('new_status')

            valid_statuses = [c[0] for c in LeadStatus.choices]

            if new_status not in valid_statuses:

                return JsonResponse({'success': False, 'error': f"Invalid status '{new_status}'."}, status=400)



            with transaction.atomic():

                for lead in leads:

                    if not can_access_lead(user, lead):

                        errors.append(f"Permission denied for lead #{lead.id}")

                        continue

                    try:

                        change_lead_status(lead, new_status, user, remarks=f"Bulk updated to {new_status}")

                        updated_count += 1

                    except Exception as e:

                        errors.append(f"Lead #{lead.id}: {str(e)}")



        elif action == 'reassign_telecaller':

            telecaller_id = data.get('telecaller_id')

            target_user = get_object_or_404(User, id=telecaller_id, role=UserRole.TELECALLER)

            from .handoff_service import reassign_lead

            with transaction.atomic():

                for lead in leads:

                    if not can_access_lead(user, lead):

                        errors.append(f"Permission denied for lead #{lead.id}")

                        continue

                    try:

                        reassign_lead(lead, to_user=target_user, to_role='TELECALLER', reason='Bulk telecaller reassignment', assigned_by=user)

                        updated_count += 1

                    except Exception as e:

                        errors.append(f"Lead #{lead.id}: {str(e)}")



        elif action in ('reassign_counselor', 'handoff_counselor'):

            counselor_id = data.get('counselor_id') or data.get('counselor')

            if not counselor_id:

                return JsonResponse({'success': False, 'error': 'Counselor ID is required.'}, status=400)

            target_user = get_object_or_404(User, id=counselor_id, role=UserRole.COUNSELOR)

            reason = data.get('reason', 'Bulk counselor reassignment').strip() or 'Bulk counselor reassignment'

            from .handoff_service import handoff_to_counselor

            with transaction.atomic():

                for lead in leads:

                    if not can_access_lead(user, lead):

                        errors.append(f"Permission denied for lead #{lead.id}")

                        continue

                    try:

                        handoff_to_counselor(lead, counselor=target_user, assigned_by=user, reason=reason)

                        updated_count += 1

                    except Exception as e:

                        errors.append(f"Lead #{lead.id}: {str(e)}")



        elif action == 'category_update':

            new_category = data.get('new_category')

            valid_categories = [c[0] for c in LeadCategory.choices]

            if new_category not in valid_categories:

                return JsonResponse({'success': False, 'error': f"Invalid category '{new_category}'. Choose from {valid_categories}"}, status=400)



            with transaction.atomic():

                for lead in leads:

                    if not can_access_lead(user, lead):

                        errors.append(f"Permission denied for lead #{lead.id}")

                        continue

                    try:

                        old_cat = lead.category

                        lead.category = new_category

                        lead.save(update_fields=['category', 'updated_at'])

                        log_activity(

                            user=user,

                            action="Lead Category Updated",

                            description=f"Bulk updated category from '{old_cat}' to '{new_category}'.",

                            object_type="Lead",

                            object_id=lead.id,

                            request=request

                        )

                        updated_count += 1

                    except Exception as e:

                        errors.append(f"Lead #{lead.id}: {str(e)}")

        else:

            return JsonResponse({'success': False, 'error': f"Unknown bulk action '{action}'"}, status=400)



        return JsonResponse({

            'success': True,

            'updated_count': updated_count,

            'errors': errors

        })

    except Exception as e:

        logger.exception("Bulk action failed: %s", e)

        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@admin_required

def admin_retry_pending_assignments(request):

    from .assignment import retry_pending_assignments

    branch_id = request.GET.get('branch_id') or request.POST.get('branch_id')

    branch = Branch.objects.filter(id=branch_id).first() if branch_id else None

    assigned, remaining = retry_pending_assignments(branch=branch, user=request.user)

    if assigned > 0:

        messages.success(request, f"Successfully assigned {assigned} pending lead(s). {remaining} lead(s) still pending.")

    else:

        if remaining > 0:

            messages.warning(request, f"Could not assign pending leads. Please verify branch telecaller allocations total exactly 100%. ({remaining} lead(s) still pending)")

        else:

            messages.info(request, "No pending leads found to assign.")

    return redirect(request.META.get('HTTP_REFERER') or reverse('admin_leads_list'))

