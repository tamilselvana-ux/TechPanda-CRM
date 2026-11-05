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

def receptionist_dashboard(request):

    """

    Dedicated dashboard for the Receptionist role.

    Displays:

      1. Total walk-in leads registered today.

      2. Leads awaiting Counselor assignment.

      3. Leads assigned today.

      4. Total walk-in leads this month.

    Lists walk-in visitors for the Receptionist's branch with quick counselor assignment,

    visitor status updates, and new student check-in registration modal.

    """

    user = request.user

    if not (user.is_admin_user or user.role in (UserRole.RECEPTIONIST, UserRole.BRANCH_HEAD)):

        raise PermissionDenied("You do not have permission to access the Receptionist dashboard.")



    # Determine branch

    if user.is_receptionist_user or user.is_branch_head_user:

        branch = user.branch

    else:

        # Admin or Superuser

        branch_id = request.GET.get('branch', '').strip()

        branch = Branch.objects.filter(pk=branch_id).first() if branch_id else user.branch or Branch.objects.filter(status='Active').first()



    search_query = request.GET.get('search', '').strip()

    status_filter = request.GET.get('status_filter', '').strip()

    assignment_filter = request.GET.get('assignment_filter', '').strip()

    lead_type_filter = request.GET.get('lead_type_filter', '').strip()

    period = request.GET.get('period', '').strip()

    from_date = request.GET.get('from_date', '').strip()

    to_date = request.GET.get('to_date', '').strip()



    # Base walkin queryset for this branch: manual walk-ins and Admin-configured Google Sheets leads

    walkin_qs = Lead.objects.filter(

        Q(source__iexact='Walk-in') |

        Q(channel__name__iexact='Walk-in') |

        Q(source__iexact='Google Sheets') |

        Q(channel__name__iexact='Google Sheets') |

        Q(sheet_mappings__isnull=False) |

        Q(is_offline=True)

    ).distinct().select_related('branch', 'assigned_counselor', 'channel', 'product').order_by('-updated_at')



    if branch:

        walkin_qs = walkin_qs.filter(Q(branch=branch) | Q(secondary_branches=branch)).distinct()

    elif not user.is_admin_user:

        walkin_qs = walkin_qs.none()



    # KPI summary cards calculation

    today = timezone.localdate()

    today_start = timezone.make_aware(datetime.combine(today, time.min))

    today_end = timezone.make_aware(datetime.combine(today, time.max))



    month_start_date = today.replace(day=1)

    month_start = timezone.make_aware(datetime.combine(month_start_date, time.min))



    # 1. Total walk-in leads registered today

    total_today = walkin_qs.filter(created_at__range=(today_start, today_end)).count()

    # 2. Leads awaiting Counselor assignment

    awaiting_assignment = walkin_qs.filter(assigned_counselor__isnull=True).count()

    # 3. Leads assigned today

    assigned_today = walkin_qs.filter(

        assigned_counselor__isnull=False

    ).filter(

        Q(center_visit_date__range=(today_start, today_end)) |

        Q(updated_at__range=(today_start, today_end))

    ).count()

    # 4. Total walk-in leads this month

    total_this_month = walkin_qs.filter(created_at__range=(month_start, today_end)).count()



    # Apply filters to table queryset

    table_qs = walkin_qs

    if period == 'today':

        table_qs = table_qs.filter(created_at__range=(today_start, today_end))

    elif period == 'week':

        week_start = timezone.make_aware(datetime.combine(today - timedelta(days=today.weekday()), time.min))

        table_qs = table_qs.filter(created_at__range=(week_start, today_end))

    elif period == 'month':

        table_qs = table_qs.filter(created_at__range=(month_start, today_end))

    elif from_date or to_date:

        if from_date:

            try:

                fd = datetime.strptime(from_date, "%Y-%m-%d").date()

                fd_start = timezone.make_aware(datetime.combine(fd, time.min))

                table_qs = table_qs.filter(created_at__gte=fd_start)

            except ValueError:

                pass

        if to_date:

            try:

                td = datetime.strptime(to_date, "%Y-%m-%d").date()

                td_end = timezone.make_aware(datetime.combine(td, time.max))

                table_qs = table_qs.filter(created_at__lte=td_end)

            except ValueError:

                pass



    if status_filter:

        table_qs = table_qs.filter(visitor_status=status_filter)

    if assignment_filter == 'unassigned':

        table_qs = table_qs.filter(assigned_counselor__isnull=True)

    elif assignment_filter == 'assigned':

        table_qs = table_qs.filter(assigned_counselor__isnull=False)



    if lead_type_filter == 'new':

        table_qs = table_qs.filter(duplicate_records__isnull=True).exclude(sheet_mappings__row_index__gt=2)

    elif lead_type_filter == 'existing':

        table_qs = table_qs.filter(

            Q(duplicate_records__isnull=False) | Q(sheet_mappings__isnull=False)

        ).distinct()



    if search_query:

        search_filter = (

            Q(name__icontains=search_query) |

            Q(phone__icontains=search_query) |

            Q(token_number__icontains=search_query) |

            Q(notes__icontains=search_query)

        )

        if search_query.isdigit():

            search_filter |= Q(id=int(search_query))

        table_qs = table_qs.filter(search_filter)



    paginator = Paginator(table_qs, 20)

    page_obj = paginator.get_page(request.GET.get('page'))



    # Identify New Lead vs Existing Lead vs Ambiguous Match for each displayed lead

    from .duplicates import normalize_phone, normalize_email

    displayed_leads = list(page_obj.object_list)

    lead_ids = [l.id for l in displayed_leads]



    duplicate_records_map = {}

    if lead_ids:

        for d in DuplicateLeadRecord.objects.filter(original_lead_id__in=lead_ids):

            duplicate_records_map.setdefault(d.original_lead_id, []).append(d)



    for lead in displayed_leads:

        dups = duplicate_records_map.get(lead.id, [])

        is_ambiguous = any(

            d.action_taken == 'AMBIGUOUS_MATCH_FLAGGED' or 'ambiguous' in (d.duplicate_reason or '').lower()

            for d in dups

        )



        is_sheets = (

            (lead.source and lead.source.lower() == 'google sheets') or

            (lead.channel and lead.channel.name.lower() == 'google sheets') or

            lead.sheet_mappings.exists()

        )

        lead.source_display = 'Google Sheets' if is_sheets else (lead.source or 'Walk-in')



        if is_ambiguous:

            lead.lead_type = 'Ambiguous Match'

            lead.lead_type_badge = 'warning'

            lead.is_existing_lead = True

            lead.is_ambiguous = True

        elif dups or lead.sheet_mappings.count() > 1:

            lead.lead_type = 'Existing Lead'

            lead.lead_type_badge = 'info'

            lead.is_existing_lead = True

            lead.is_ambiguous = False

        else:

            clean_p = normalize_phone(lead.phone)

            clean_e = normalize_email(lead.email)

            has_other_match = False

            if clean_p and len(clean_p) >= 10:

                p_tail = clean_p[-10:]

                has_other_match = Lead.objects.filter(

                    Q(phone__endswith=p_tail) | Q(alternate_phone__endswith=p_tail)

                ).exclude(id=lead.id).exists()

            if not has_other_match and clean_e:

                has_other_match = Lead.objects.filter(email__iexact=clean_e).exclude(id=lead.id).exists()



            has_history = (

                lead.assignment_history.count() > 1 or

                lead.followups.exists() or

                lead.calls.exists() or

                lead.status_history.count() > 1

            )



            if has_other_match or has_history:

                lead.lead_type = 'Existing Lead'

                lead.lead_type_badge = 'info'

                lead.is_existing_lead = True

                lead.is_ambiguous = False

            else:

                lead.lead_type = 'New Lead'

                lead.lead_type_badge = 'success'

                lead.is_existing_lead = False

                lead.is_ambiguous = False



    # Counselors strictly belonging to this branch (active only)

    if branch:

        counselors = list(User.objects.filter(

            role=UserRole.COUNSELOR,

            branch=branch,

            is_active=True

        ).order_by('first_name', 'username'))

    else:

        counselors = []



    all_branches = Branch.objects.filter(status='Active').order_by('name') if user.is_admin_user else []

    from products.models import Product

    products = list(Product.objects.filter(status='Active').order_by('name'))



    return render(request, 'receptionist/dashboard.html', {

        'page_obj': page_obj,

        'branch': branch,

        'all_branches': all_branches,

        'counselors': counselors,

        'products': products,

        'total_today': total_today,

        'awaiting_assignment': awaiting_assignment,

        'assigned_today': assigned_today,

        'total_this_month': total_this_month,

        'search_query': search_query,

        'status_filter': status_filter,

        'assignment_filter': assignment_filter,

        'lead_type_filter': lead_type_filter,

        'period': period,

        'from_date': from_date,

        'to_date': to_date,

        'has_counselors': len(counselors) > 0,

    })


@login_required

def receptionist_lead_history(request, pk):

    """

    Dedicated view for Receptionist to review complete available lead history:

    - Student info (read-only)

    - Counselor assignment history & audit trail

    - Status history (read-only)

    - Communication history: Follow-ups, Call history, Notes & remarks, WhatsApp messages

    - Intake / Import info: Google Sheets mapping, Registration date, Duplicate records, Matching leads

    Enforces strict branch isolation for Receptionist.

    Supports both JSON response (for modal / drawer) and HTML page rendering.

    """

    user = request.user

    if not (user.is_admin_user or user.is_receptionist_user):

        raise PermissionDenied("You do not have permission to view Receptionist lead history.")



    lead = get_object_or_404(

        Lead.objects.select_related('branch', 'assigned_counselor', 'assigned_telecaller', 'channel', 'product'),

        pk=pk

    )



    if user.is_receptionist_user and lead.branch_id != user.branch_id:

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':

            return JsonResponse({'success': False, 'error': 'Permission denied: Cannot access lead from another branch.'}, status=403)

        raise PermissionDenied("You do not have permission to view leads belonging to another branch.")



    # 1. Student Info

    student_info = {

        'id': lead.id,

        'token_number': lead.token_number or f"WI-{lead.id}",

        'name': lead.name,

        'phone': lead.phone,

        'email': lead.email or 'Not provided',

        'course': lead.product.name if lead.product else (getattr(lead, 'course_display', None) or lead.category or 'Not specified'),

        'branch': lead.branch.name if lead.branch else 'Unassigned',

        'branch_id': lead.branch_id,

        'source': lead.source or (lead.channel.name if lead.channel else 'Direct'),

        'channel': lead.channel.name if lead.channel else 'Direct',

        'created_at': lead.created_at.strftime('%Y-%m-%d %H:%M') if lead.created_at else '',

        'updated_at': lead.updated_at.strftime('%Y-%m-%d %H:%M') if lead.updated_at else '',

        'center_visit_date': lead.center_visit_date.strftime('%Y-%m-%d %H:%M') if lead.center_visit_date else '',

        'status': lead.status,

        'visitor_status': getattr(lead, 'visitor_status', ''),

        'assignment_status': getattr(lead, 'assignment_status', 'Pending Assignment'),

        'current_counselor': (lead.assigned_counselor.get_full_name() or lead.assigned_counselor.username) if lead.assigned_counselor else None,

        'current_counselor_id': lead.assigned_counselor_id,

        'notes': lead.notes or '',

    }



    # 2. Assignment History

    assignments = []

    for h in lead.assignment_history.select_related('from_user', 'to_user', 'assigned_by').order_by('-created_at'):

        assignments.append({

            'id': h.id,

            'from_user': (h.from_user.get_full_name() or h.from_user.username) if h.from_user else (h.from_role or 'None'),

            'to_user': (h.to_user.get_full_name() or h.to_user.username) if h.to_user else (h.to_role or 'None'),

            'from_role': h.from_role or '',

            'to_role': h.to_role or '',

            'assigned_by': (h.assigned_by.get_full_name() or h.assigned_by.username) if h.assigned_by else 'System',

            'reason': h.reason or 'No reason recorded',

            'created_at': h.created_at.strftime('%Y-%m-%d %H:%M') if h.created_at else '',

        })



    # 3. Status History

    status_history = []

    for s in lead.status_history.select_related('changed_by').order_by('-created_at'):

        status_history.append({

            'id': s.id,

            'old_status': s.old_status or 'Initial',

            'new_status': s.new_status,

            'changed_by': (s.changed_by.get_full_name() or s.changed_by.username) if s.changed_by else 'System',

            'remarks': s.remarks or '',

            'created_at': s.created_at.strftime('%Y-%m-%d %H:%M') if s.created_at else '',

        })



    # 4. Follow-up records

    followups = []

    for f in lead.followups.select_related('assigned_user').order_by('-follow_up_date'):

        dt_str = f.follow_up_date.strftime('%Y-%m-%d') if f.follow_up_date else ''

        if getattr(f, 'follow_up_time', None):

            dt_str += f" {f.follow_up_time.strftime('%H:%M')}"

        assigned_name = (f.assigned_user.get_full_name() or f.assigned_user.username) if getattr(f, 'assigned_user', None) else 'System'

        followups.append({

            'id': f.id,

            'scheduled_time': dt_str,

            'status': f.status,

            'notes': f.notes or '',

            'scheduled_by': assigned_name,

        })



    # 5. Call History

    calls = []

    for c in lead.calls.select_related('caller').order_by('-created_at'):

        call_time_val = getattr(c, 'call_started_at', None) or getattr(c, 'created_at', None)

        calls.append({

            'id': c.id,

            'call_time': call_time_val.strftime('%Y-%m-%d %H:%M') if call_time_val else '',

            'caller': (c.caller.get_full_name() or c.caller.username) if c.caller else 'Unknown',

            'outcome': getattr(c, 'call_outcome', '') or getattr(c, 'outcome', 'No outcome'),

            'duration': getattr(c, 'duration', 0) or 0,

            'status': getattr(c, 'call_status', '') or getattr(c, 'status', ''),

            'notes': c.notes or '',

        })



    # 6. WhatsApp Interactions

    whatsapp_data = []

    try:

        from chat.models import Conversation

        from .duplicates import normalize_phone

        clean_p = normalize_phone(lead.phone)

        if clean_p:

            p_tail = clean_p[-10:] if len(clean_p) >= 10 else clean_p

            conv_qs = Conversation.objects.filter(

                Q(phone_number__endswith=p_tail) | Q(phone_number__icontains=clean_p)

            )

            for conv in conv_qs:

                msgs = []

                for m in conv.messages.order_by('-created_at')[:5]:

                    msgs.append({

                        'sender_type': m.sender_type,

                        'message_text': m.message_text,

                        'created_at': m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else '',

                        'status': m.status,

                    })

                whatsapp_data.append({

                    'conversation_id': conv.id,

                    'customer_name': conv.customer_name,

                    'phone_number': conv.phone_number,

                    'last_message': conv.last_message,

                    'last_message_time': conv.last_message_time.strftime('%Y-%m-%d %H:%M') if conv.last_message_time else '',

                    'unread_count': conv.unread_count,

                    'recent_messages': msgs,

                })

    except Exception as e:

        logger.warning("Error fetching WhatsApp history for lead %s: %s", lead.id, e)



    # 7. Activities

    activities = []

    for a in Activity.objects.filter(object_type='Lead', object_id=str(lead.id)).select_related('user').order_by('-timestamp')[:20]:

        activities.append({

            'action': a.action,

            'description': a.description,

            'user': (a.user.get_full_name() or a.user.username) if a.user else 'System',

            'created_at': a.timestamp.strftime('%Y-%m-%d %H:%M') if getattr(a, 'timestamp', None) else '',

        })



    # 8. Google Sheets & Intake Details

    sheet_info = []

    for sm in lead.sheet_mappings.select_related('connection').all():

        last_sync = sm.connection.sync_histories.order_by('-timestamp').first()

        s_dict = {

            'connection_name': sm.connection.name,

            'row_index': sm.row_index,

            'row_identifier': sm.row_identifier,

            'source_status': sm.source_status,

            'mapped_at': sm.created_at.strftime('%Y-%m-%d %H:%M') if sm.created_at else '',

            'last_sync_time': last_sync.timestamp.strftime('%Y-%m-%d %H:%M') if (last_sync and getattr(last_sync, 'timestamp', None)) else 'Never',

            'last_sync_status': last_sync.status if last_sync else 'Unknown',

        }

        if user.is_admin_user:

            s_dict['spreadsheet_url'] = sm.connection.spreadsheet_url

        sheet_info.append(s_dict)



    # 9. Duplicate / Matching Records

    from .duplicates import find_all_matching_leads

    matching_leads_raw = find_all_matching_leads(phone=lead.phone, email=lead.email, name=lead.name, exclude_id=lead.id)

    matching_leads = []

    for m in matching_leads_raw:

        matching_leads.append({

            'id': m.id,

            'name': m.name,

            'phone': m.phone,

            'email': m.email or '',

            'branch': m.branch.name if m.branch else 'Unassigned',

            'status': m.status,

            'counselor': (m.assigned_counselor.get_full_name() or m.assigned_counselor.username) if m.assigned_counselor else None,

            'created_at': m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else '',

        })



    duplicate_audit = []

    for d in lead.duplicate_records.select_related('branch', 'existing_branch').order_by('-submitted_at')[:10]:

        duplicate_audit.append({

            'source': d.source,

            'duplicate_reason': d.duplicate_reason,

            'action_taken': d.action_taken,

            'submitted_at': d.submitted_at.strftime('%Y-%m-%d %H:%M') if d.submitted_at else '',

            'notes': d.notes,

        })



    # Counselors available for assignment in this branch

    branch = lead.branch or user.branch

    counselors = []

    if branch:

        counselor_users = User.objects.filter(role=UserRole.COUNSELOR, branch=branch, is_active=True).order_by('first_name', 'username')

        for c in counselor_users:

            counselors.append({

                'id': c.id,

                'name': c.get_full_name() or c.username,

                'username': c.username

            })



    data_payload = {

        'success': True,

        'student': student_info,

        'assignments': assignments,

        'status_history': status_history,
        'timeline_count': (len(calls) if calls else 0) + (len(status_history) if status_history else 0) + (len(followups) if followups else 0),

        'followups': followups,

        'calls': calls,

        'whatsapp': whatsapp_data,

        'activities': activities,

        'sheet_info': sheet_info,

        'is_google_sheet_origin': len(sheet_info) > 0,

        'matching_leads': matching_leads,

        'duplicate_audit': duplicate_audit,

        'counselors': counselors,

        'has_counselors': len(counselors) > 0,

    }



    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':

        return JsonResponse(data_payload)



    return render(request, 'receptionist/lead_history.html', {

        'lead': lead,

        'student': student_info,

        'assignments': assignments,

        'status_history': status_history,
        'timeline_count': (len(calls) if calls else 0) + (len(status_history) if status_history else 0) + (len(followups) if followups else 0),

        'followups': followups,

        'calls': calls,

        'whatsapp': whatsapp_data,

        'activities': activities,

        'sheet_info': sheet_info,

        'matching_leads': matching_leads,

        'duplicate_audit': duplicate_audit,

        'counselors': counselors,

        'has_counselors': len(counselors) > 0,

        'branch': branch,

    })


@login_required

def receptionist_check_existing_lead(request):

    """

    Real-time duplicate detection endpoint for the Receptionist student check-in modal.

    Searches by normalized phone, email, and name.

    Returns matching leads with full details so receptionist can review history or assign counselor directly.

    """

    user = request.user

    if not (user.is_admin_user or user.is_receptionist_user):

        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)



    phone = request.GET.get('phone', '').strip()

    email = request.GET.get('email', '').strip()

    name = request.GET.get('name', '').strip()



    if not (phone or email or name):

        return JsonResponse({'success': True, 'matches': []})



    from .duplicates import find_all_matching_leads

    matches = find_all_matching_leads(phone=phone, email=email, name=name)



    match_list = []

    for m in matches:

        match_list.append({

            'id': m.id,

            'name': m.name,

            'phone': m.phone,

            'email': m.email or '',

            'branch': m.branch.name if m.branch else 'Unassigned',

            'branch_id': m.branch_id,

            'status': m.status,

            'visitor_status': getattr(m, 'visitor_status', ''),

            'source': m.source or (m.channel.name if m.channel else 'Direct'),

            'assigned_counselor': (m.assigned_counselor.get_full_name() or m.assigned_counselor.username) if m.assigned_counselor else None,
            'assigned_counselor_id': m.assigned_counselor_id if m.assigned_counselor_id else None,
            'course_id': getattr(m, 'product_id', None),
            'course_name': m.product.name if getattr(m, 'product', None) else (getattr(m, 'course_name', '') or ''),
            'category': getattr(m, 'category', '') or 'Training',

            'created_at': m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else ''

        })



    return JsonResponse({

        'success': True,

        'has_matches': len(match_list) > 0,

        'count': len(match_list),

        'matches': match_list

    })


@login_required

def admin_walkin_desk(request):

    """

    Reception & Walk-in Desk view for tracking in-person branch visits,

    issuing token passes, and managing live counselor assignments.

    """

    user = request.user

    if user.is_receptionist_user:

        return redirect('receptionist_dashboard')

    if not (user.is_admin_user or user.role in (UserRole.SALES_HEAD, UserRole.BRANCH_HEAD, UserRole.COUNSELOR, UserRole.RECEPTIONIST)):

        raise PermissionDenied("You do not have permission to access the reception desk.")



    branch_filter = request.GET.get('branch', '').strip()

    status_filter = request.GET.get('status_filter', '').strip()

    search_query = request.GET.get('search', '').strip()



    # Walk-in leads base query - matches direct walk-in, QR form, and walk-in channels

    walkin_qs = Lead.objects.filter(

        Q(source__icontains='Walk-in') | Q(channel__name__icontains='Walk-in')

    ).select_related('branch', 'assigned_counselor', 'channel').order_by('-created_at')



    # Scope permissions

    if not user.is_admin_user:

        from accounts.permissions import get_accessible_branch_ids

        accessible_branch_ids = get_accessible_branch_ids(user)

        if accessible_branch_ids:

            walkin_qs = walkin_qs.filter(branch_id__in=accessible_branch_ids)



    if branch_filter:

        walkin_qs = walkin_qs.filter(branch_id=branch_filter)



    # Date range calculations

    import datetime

    now = timezone.now()

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    yesterday_start = today_start - datetime.timedelta(days=1)

    week_start = today_start - datetime.timedelta(days=7)



    date_filter = request.GET.get('date_filter', 'today').strip().lower()



    # Base counts for segmented tabs

    count_today = walkin_qs.filter(Q(created_at__gte=today_start) | Q(center_visit_date__gte=today_start)).count()

    count_yesterday = walkin_qs.filter(

        (Q(created_at__gte=yesterday_start) & Q(created_at__lt=today_start)) |

        (Q(center_visit_date__gte=yesterday_start) & Q(center_visit_date__lt=today_start))

    ).count()

    count_week = walkin_qs.filter(Q(created_at__gte=week_start) | Q(center_visit_date__gte=week_start)).count()

    count_all = walkin_qs.count()



    # Apply date filter (defaults to 'today' so table view matches today KPI)

    if date_filter == 'today':

        walkin_qs = walkin_qs.filter(Q(created_at__gte=today_start) | Q(center_visit_date__gte=today_start))

    elif date_filter == 'yesterday':

        walkin_qs = walkin_qs.filter(

            (Q(created_at__gte=yesterday_start) & Q(created_at__lt=today_start)) |

            (Q(center_visit_date__gte=yesterday_start) & Q(center_visit_date__lt=today_start))

        )

    elif date_filter == 'week':

        walkin_qs = walkin_qs.filter(Q(created_at__gte=week_start) | Q(center_visit_date__gte=week_start))

    # 'all' applies no date filter



    # Accurate KPI counts matching active date scope

    active_range_total = walkin_qs.count()

    waiting_count = walkin_qs.filter(visitor_status='Waiting').count()

    in_consultation_count = walkin_qs.filter(visitor_status='In Consultation').count()

    completed_count = walkin_qs.filter(visitor_status='Completed').count()



    if status_filter:

        walkin_qs = walkin_qs.filter(visitor_status=status_filter)



    if search_query:

        walkin_qs = walkin_qs.filter(

            Q(name__icontains=search_query) |

            Q(phone__icontains=search_query) |

            Q(token_number__icontains=search_query) |

            Q(notes__icontains=search_query)

        )



    paginator = Paginator(walkin_qs, 20)

    page_obj = paginator.get_page(request.GET.get('page'))



    if user.is_admin_user:

        branches = Branch.objects.filter(status='Active')

    else:

        from accounts.permissions import get_accessible_branch_ids

        branches = Branch.objects.filter(id__in=get_accessible_branch_ids(user), status='Active')



    counselors_qs = User.objects.filter(role=UserRole.COUNSELOR, is_active=True).select_related('branch')

    if branch_filter:

        counselors_qs = counselors_qs.filter(branch_id=branch_filter)

    elif not user.is_admin_user and user.branch_id:

        counselors_qs = counselors_qs.filter(branch_id=user.branch_id)

    counselors = list(counselors_qs.order_by('first_name', 'username'))



    return render(request, 'admin/walkin_desk.html', {

        'page_obj': page_obj,

        'branches': branches,

        'counselors': counselors,

        'active_range_total': active_range_total,

        'total_walkins_today': count_today,

        'waiting_count': waiting_count,

        'in_consultation_count': in_consultation_count,

        'completed_count': completed_count,

        'branch_filter': branch_filter,

        'status_filter': status_filter,

        'date_filter': date_filter,

        'count_today': count_today,

        'count_yesterday': count_yesterday,

        'count_week': count_week,

        'count_all': count_all,

        'search_query': search_query,

    })


@login_required

@require_POST

def admin_walkin_create(request):

    """

    Creates/checks-in a new walk-in prospect at reception desk.

    Generates token number, records center visit date, and optionally assigns to counselor.

    """

    user = request.user

    if not (user.is_admin_user or user.role in (UserRole.SALES_HEAD, UserRole.BRANCH_HEAD, UserRole.COUNSELOR, UserRole.RECEPTIONIST)):

        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)



    try:

        if request.content_type == 'application/json':

            data = json.loads(request.body)

        else:

            data = request.POST



        name = (data.get('name') or '').strip()

        phone = (data.get('phone') or '').strip()

        email = (data.get('email') or '').strip()

        branch_id = data.get('branch_id')

        category = data.get('category', LeadCategory.TRAINING)

        counselor_id = data.get('counselor_id')

        product_id = data.get('product_id') or data.get('product')

        notes = (data.get('notes') or data.get('remarks') or '').strip()



        if not name or not phone:

            return JsonResponse({'success': False, 'error': 'Name and Phone are required.'}, status=400)



        product = None

        if product_id:

            from products.models import Product

            try:

                product = Product.objects.get(pk=product_id)

            except (Product.DoesNotExist, ValueError):

                pass



        # Enforce branch scope: Receptionists are strictly bound to their assigned branch

        if user.is_receptionist_user:

            if not user.branch:

                return JsonResponse({'success': False, 'error': 'Receptionist must be assigned to a branch.'}, status=400)

            branch = user.branch

        else:

            branch = get_object_or_404(Branch, pk=branch_id) if branch_id else user.branch



        # Validate counselor belongs to the same branch and is active

        counselor = None

        if counselor_id:

            counselor = get_object_or_404(User, pk=counselor_id, role=UserRole.COUNSELOR, is_active=True)

            if branch and counselor.branch_id and counselor.branch_id != branch.id:

                return JsonResponse({'success': False, 'error': 'Selected counselor belongs to a different branch.'}, status=400)



        # Support checking in an existing matching lead without creating a duplicate

        existing_lead_id = data.get('existing_lead_id')

        if existing_lead_id:

            lead = get_object_or_404(Lead, pk=existing_lead_id)

            if user.is_receptionist_user and lead.branch_id != user.branch_id:

                return JsonResponse({'success': False, 'error': 'Permission denied: Cannot check in lead from another branch.'}, status=403)

            lead.center_visit_date = timezone.now()

            lead.visitor_status = VisitorStatus.IN_CONSULTATION if counselor else VisitorStatus.WAITING

            if counselor:

                from .handoff_service import handoff_to_counselor

                handoff_to_counselor(lead, counselor=counselor, assigned_by=user, reason='Reception desk visit check-in')

                lead.assignment_status = 'Assigned'

            lead.save(update_fields=['center_visit_date', 'visitor_status', 'assignment_status', 'updated_at'])

            return JsonResponse({

                'success': True,

                'lead_id': lead.id,

                'token_number': lead.token_number or f"WI-{lead.id}",

                'message': f"Existing student '{lead.name}' checked in successfully."

            })



        # Check for matching existing leads using normalized duplicate detection

        from .duplicates import find_all_matching_leads

        matches = find_all_matching_leads(phone=phone, email=email, name=name)

        force_create = data.get('force_create', False)



        if matches and not force_create:

            match_list = []

            for m in matches:

                match_list.append({

                    'id': m.id,

                    'name': m.name,

                    'phone': m.phone,

                    'email': m.email or '',

                    'branch': m.branch.name if m.branch else 'Unassigned',

                    'branch_id': m.branch_id,

                    'status': m.status,

                    'visitor_status': getattr(m, 'visitor_status', ''),

                    'source': m.source or (m.channel.name if m.channel else 'Direct'),

                    'assigned_counselor': (m.assigned_counselor.get_full_name() or m.assigned_counselor.username) if m.assigned_counselor else None,

                    'created_at': m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else ''

                })

            return JsonResponse({

                'success': False,

                'is_duplicate': True,

                'message': f"Found {len(matches)} matching existing student record(s) in CRM. You can review history or assign counselor directly.",

                'matches': match_list

            }, status=200)



        walkin_channel, _ = Channel.objects.get_or_create(name='Walk-in', defaults={'status': 'Active'})



        # Generate daily token

        today_local = timezone.localdate()

        date_str = today_local.strftime('%Y%m%d')

        start_of_today_seq = timezone.make_aware(datetime.combine(today_local, time.min))

        end_of_today_seq = timezone.make_aware(datetime.combine(today_local, time.max))

        seq = Lead.objects.filter(created_at__range=(start_of_today_seq, end_of_today_seq), source='Walk-in').count() + 1

        token_number = f"WI-{date_str}-{seq:03d}"



        from .intake import CentralizedLeadIntakeService
        intake_res = CentralizedLeadIntakeService.ingest(
            phone=phone,
            source='Walk-in',
            channel_name='Walk-in',
            name=name,
            email=email,
            branch=branch,
            product=product,
            note=notes,
            token_number=token_number,
            center_visit_date=timezone.now(),
            visitor_status=VisitorStatus.IN_CONSULTATION if counselor else VisitorStatus.WAITING,
            activity_user=user,
            incoming_timestamp=timezone.now(),
        )
        lead = intake_res.lead
        lead.category = category
        lead.is_offline = True
        if intake_res.created:
            lead.status = LeadStatus.VISITED
        lead.save(update_fields=['category', 'is_offline', 'status', 'updated_at'])



        log_activity(

            user=user,

            action="Walk-in Visitor Checked In",

            description=f"Walk-in prospect '{lead.name}' ({lead.phone}) checked in at {branch.name if branch else 'Reception'}. Token: #{token_number}",

            object_type="Lead",

            object_id=lead.id,

            request=request

        )



        # If immediate counselor assignment was selected

        if counselor:

            from .handoff_service import handoff_to_counselor

            handoff_to_counselor(lead, counselor=counselor, assigned_by=user, reason='Reception desk immediate assignment')

            lead.visitor_status = VisitorStatus.IN_CONSULTATION

            lead.assignment_status = 'Assigned'

            lead.save(update_fields=['visitor_status', 'assignment_status', 'updated_at'])



            from activities.services import create_notification

            create_notification(

                recipient=counselor,

                title="Walk-in Visitor Waiting",

                message=f"{lead.name} (Token: #{token_number}) is waiting for consultation in {branch.name if branch else 'reception'}.",

                notification_type='info',

                link=reverse('counselor_lead_detail', args=[lead.id])

            )



        return JsonResponse({

            'success': True,

            'lead_id': lead.id,

            'token_number': token_number,

            'message': f"Visitor checked in with Token #{token_number}."

        })

    except Exception as e:

        logger.exception("admin_walkin_create failed: %s", e)

        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required

@require_POST

def admin_walkin_assign_counselor(request, pk):

    """

    Assigns a waiting walk-in visitor to an available branch counselor.

    Updates visitor status to 'In Consultation' and dispatches notifications.

    Uses select_for_update() inside atomic transaction to prevent race conditions.

    """

    user = request.user

    if not (user.is_admin_user or user.role in (UserRole.SALES_HEAD, UserRole.BRANCH_HEAD, UserRole.COUNSELOR, UserRole.RECEPTIONIST)):

        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)



    if user.is_receptionist_user and not user.branch_id:

        return JsonResponse({'success': False, 'error': 'Your receptionist account is not assigned to any branch.'}, status=403)



    if request.content_type == 'application/json':

        try:

            data = json.loads(request.body)

        except Exception:

            data = {}

    else:

        data = request.POST



    counselor_id = data.get('counselor_id')

    reason = (data.get('reason') or 'Assigned at Reception Desk').strip()



    if not counselor_id:

        return JsonResponse({'success': False, 'error': 'Counselor ID is required.'}, status=400)



    try:

        counselor = User.objects.get(pk=counselor_id, role=UserRole.COUNSELOR, is_active=True)

    except User.DoesNotExist:

        return JsonResponse({'success': False, 'error': 'Selected counselor was not found or is inactive.'}, status=404)



    # Counselor must belong to the receptionist's branch

    if user.is_receptionist_user and counselor.branch_id != user.branch_id:

        return JsonResponse({'success': False, 'error': 'Cannot assign to a counselor outside your branch.'}, status=400)



    from .handoff_service import handoff_to_counselor

    with transaction.atomic():

        try:

            lead = Lead.objects.select_for_update().get(pk=pk)

        except Lead.DoesNotExist:

            return JsonResponse({'success': False, 'error': 'Lead not found.'}, status=404)



        # Cross-branch prevention for Receptionists

        if user.is_receptionist_user and lead.branch_id != user.branch_id:

            return JsonResponse({'success': False, 'error': 'Permission denied: Cannot assign leads from another branch.'}, status=403)



        if lead.branch_id and counselor.branch_id and counselor.branch_id != lead.branch_id:

            return JsonResponse({'success': False, 'error': 'Counselor must belong to the same branch as the lead.'}, status=400)



        handoff_to_counselor(lead, counselor=counselor, assigned_by=user, reason=reason)

        lead.visitor_status = VisitorStatus.IN_CONSULTATION

        lead.assignment_status = 'Assigned'

        if not lead.center_visit_date:

            lead.center_visit_date = timezone.now()

        lead.save(update_fields=['visitor_status', 'assignment_status', 'center_visit_date', 'updated_at'])



        log_activity(

            user=user,

            action="Walk-in Assigned to Counselor",

            description=f"Walk-in visitor #{lead.id} ({lead.name}) assigned to Counselor '{counselor.username}'.",

            object_type="Lead",

            object_id=lead.id,

            request=request

        )



        from activities.services import create_notification

        create_notification(

            recipient=counselor,

            title="Walk-in Consultation Assigned",

            message=f"{lead.name} (Token: #{lead.token_number or lead.id}) is waiting for you in reception.",

            notification_type='info',

            link=reverse('counselor_lead_detail', args=[lead.id])

        )



    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json' or request.GET.get('format') == 'json':

        return JsonResponse({

            'success': True,

            'lead_id': lead.id,

            'counselor_name': counselor.get_full_name() or counselor.username,

            'message': f"Visitor successfully assigned to Counselor {counselor.username}."

        })

    messages.success(request, f"Visitor #{lead.id} successfully assigned to Counselor {counselor.get_full_name() or counselor.username}.")

    return redirect('receptionist_dashboard')


@login_required

@require_POST

def admin_walkin_bulk_assign_counselor(request):

    """

    Bulk assigns one or multiple walk-in leads to an available branch counselor.

    Validates receptionist branch scope and counselor branch compatibility.

    Saves assignments atomically with row-locking and dispatches notifications.

    """

    user = request.user

    if not (user.is_admin_user or user.role in (UserRole.SALES_HEAD, UserRole.BRANCH_HEAD, UserRole.COUNSELOR, UserRole.RECEPTIONIST)):

        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)



    if user.is_receptionist_user and not user.branch_id:

        return JsonResponse({'success': False, 'error': 'Your receptionist account is not assigned to any branch.'}, status=403)



    if request.content_type == 'application/json':

        try:

            data = json.loads(request.body)

        except Exception:

            data = {}

    else:

        data = request.POST



    raw_lead_ids = data.get('lead_ids') or (data.getlist('lead_ids') if hasattr(data, 'getlist') else [])

    if isinstance(raw_lead_ids, str):

        lead_ids = [int(x.strip()) for x in raw_lead_ids.split(',') if x.strip().isdigit()]

    elif isinstance(raw_lead_ids, (list, tuple)):

        lead_ids = [int(x) for x in raw_lead_ids if str(x).isdigit()]

    else:

        lead_ids = []



    counselor_id = data.get('counselor_id')

    reason = (data.get('reason') or 'Bulk assigned at Reception Desk').strip()



    if not lead_ids:

        return JsonResponse({'success': False, 'error': 'Please select at least one lead to assign.'}, status=400)



    if not counselor_id:

        return JsonResponse({'success': False, 'error': 'Counselor ID is required.'}, status=400)



    try:

        counselor = User.objects.get(pk=counselor_id, role=UserRole.COUNSELOR, is_active=True)

    except User.DoesNotExist:

        return JsonResponse({'success': False, 'error': 'Selected counselor was not found or is inactive.'}, status=404)



    # Counselor must belong to the receptionist's branch

    if user.is_receptionist_user and counselor.branch_id != user.branch_id:

        return JsonResponse({'success': False, 'error': 'Cannot assign to a counselor outside your branch.'}, status=400)



    from .handoff_service import handoff_to_counselor

    assigned_count = 0



    with transaction.atomic():

        leads = list(Lead.objects.select_for_update().filter(id__in=lead_ids))

        if not leads:

            return JsonResponse({'success': False, 'error': 'No matching leads found.'}, status=404)



        for lead in leads:

            # Cross-branch check for Receptionists

            if user.is_receptionist_user and lead.branch_id != user.branch_id:

                return JsonResponse({

                    'success': False,

                    'error': f"Permission denied: Lead #{lead.id} ('{lead.name}') belongs to a different branch."

                }, status=403)



            if lead.branch_id and counselor.branch_id and counselor.branch_id != lead.branch_id:

                return JsonResponse({

                    'success': False,

                    'error': f"Counselor must belong to the same branch as lead #{lead.id} ('{lead.name}')."

                }, status=400)



            handoff_to_counselor(lead, counselor=counselor, assigned_by=user, reason=reason)

            lead.visitor_status = VisitorStatus.IN_CONSULTATION

            lead.assignment_status = 'Assigned'

            if not lead.center_visit_date:

                lead.center_visit_date = timezone.now()

            lead.save(update_fields=['visitor_status', 'assignment_status', 'center_visit_date', 'updated_at'])



            log_activity(

                user=user,

                action="Walk-in Assigned to Counselor",

                description=f"Walk-in visitor #{lead.id} ({lead.name}) assigned to Counselor '{counselor.username}'.",

                object_type="Lead",

                object_id=lead.id,

                request=request

            )

            assigned_count += 1



        if assigned_count > 0:

            from activities.services import create_notification

            create_notification(

                recipient=counselor,

                title="Walk-in Consultations Assigned",

                message=f"{assigned_count} walk-in student(s) have been assigned to you by Reception.",

                notification_type='info',

                link=reverse('counselor_dashboard')

            )



    msg = f"Successfully assigned {assigned_count} walk-in lead(s) to Counselor {counselor.get_full_name() or counselor.username}."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json' or request.GET.get('format') == 'json':

        return JsonResponse({

            'success': True,

            'assigned_count': assigned_count,

            'counselor_name': counselor.get_full_name() or counselor.username,

            'message': msg

        })



    messages.success(request, msg)

    return redirect('receptionist_dashboard')


@login_required

@require_POST

def admin_walkin_update_status(request, pk):

    """

    Updates the visitor status of a walk-in lead (Waiting / In Consultation / Completed / No Show).

    """

    user = request.user

    if user.is_receptionist_user or not (user.is_admin_user or user.role in (UserRole.SALES_HEAD, UserRole.BRANCH_HEAD, UserRole.COUNSELOR)):

        return JsonResponse({'success': False, 'error': 'Permission denied: Receptionists cannot update lead status.'}, status=403)



    lead = get_object_or_404(Lead, pk=pk)



    # Cross-branch prevention for Receptionists

    if user.is_receptionist_user and lead.branch_id != user.branch_id:

        return JsonResponse({'success': False, 'error': 'Permission denied: Cannot update status of leads from another branch.'}, status=403)



    if request.content_type == 'application/json':

        data = json.loads(request.body)

    else:

        data = request.POST



    new_status = data.get('visitor_status')

    if new_status not in [c[0] for c in VisitorStatus.choices]:

        return JsonResponse({'success': False, 'error': f"Invalid visitor status: '{new_status}'"}, status=400)



    lead.visitor_status = new_status

    update_fields = ['visitor_status', 'updated_at']



    if new_status == VisitorStatus.COMPLETED and lead.status not in (LeadStatus.CONVERTED, LeadStatus.JOINED):

        lead.status = LeadStatus.VISITED

        update_fields.append('status')



    lead.save(update_fields=update_fields)



    log_activity(

        user=user,

        action="Walk-in Status Updated",

        description=f"Walk-in visitor #{lead.id} ({lead.name}) status changed to '{new_status}'.",

        object_type="Lead",

        object_id=lead.id,

        request=request

    )



    return JsonResponse({

        'success': True,

        'lead_id': lead.id,

        'visitor_status': new_status

    })

