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

def export_leads_csv(request):

    """

    Exports selected or filtered leads to a CSV file respecting user role visibility.

    """

    import csv

    user = request.user

    qs = Lead.objects.all().select_related('channel', 'product', 'branch', 'assigned_telecaller')



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



    lead_ids_raw = request.GET.get('lead_ids', '')

    if lead_ids_raw:

        ids = [int(i.strip()) for i in lead_ids_raw.split(',') if i.strip().isdigit()]

        qs = qs.filter(id__in=ids)

    else:

        q = request.GET.get('search', '').strip()

        if q:

            qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q))

        status = request.GET.get('status', '').strip()

        if status:

            qs = qs.filter(status=status)

        branch = request.GET.get('branch', '').strip()

        if branch:

            qs = qs.filter(branch_id=branch)

        telecaller = request.GET.get('telecaller', '').strip()

        if telecaller:

            qs = qs.filter(assigned_telecaller_id=telecaller)

        channel = request.GET.get('channel', '').strip()

        if channel:

            qs = qs.filter(channel_id=channel)

        product = request.GET.get('product', '').strip()

        if product:

            qs = qs.filter(product_id=product)



    response = HttpResponse(content_type='text/csv')

    filename = f"leads_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"

    response['Content-Disposition'] = f'attachment; filename="{filename}"'



    writer = csv.writer(response)

    writer.writerow([

        'ID', 'Name', 'Phone', 'Email', 'Branch', 'Source/Channel',

        'Status', 'Product', 'Assigned Telecaller', 'WhatsApp Opt Out', 'Created At'

    ])



    for ld in qs.iterator(chunk_size=500):

        writer.writerow([

            ld.id,

            ld.name,

            ld.phone,

            ld.email or '',

            ld.branch.name if ld.branch else '',

            ld.channel.name if ld.channel else (ld.source or ''),

            ld.status,

            ld.product.name if ld.product else '',

            ld.assigned_telecaller.get_full_name() or ld.assigned_telecaller.username if ld.assigned_telecaller else 'Unassigned',

            'Yes' if getattr(ld, 'whatsapp_opt_out', False) else 'No',

            ld.created_at.strftime('%Y-%m-%d %H:%M:%S') if ld.created_at else ''

        ])



    return response


@admin_required

def admin_duplicate_leads_export(request):

    """

    Exports filtered or all duplicate records to CSV for audit and analytics.

    """

    import csv

    from django.http import HttpResponse



    qs = DuplicateLeadRecord.objects.exclude(record_type='ORIGINAL_INGESTION').select_related('original_lead', 'branch', 'original_lead__branch').order_by('-submitted_at')



    # Apply same filters

    search_q = request.GET.get('q', '').strip()

    if search_q:

        clean_p = re.sub(r'\D', '', search_q)

        target_10 = clean_p[-10:] if len(clean_p) >= 10 else clean_p

        search_filter = (

            Q(name__icontains=search_q) |

            Q(phone__icontains=search_q) |

            Q(email__icontains=search_q) |

            Q(source__icontains=search_q)

        )

        if target_10:

            search_filter |= Q(normalized_phone__icontains=target_10)

        qs = qs.filter(search_filter)



    branch_id = request.GET.get('branch_id', '').strip()

    if branch_id and branch_id.isdigit():

        qs = qs.filter(Q(branch_id=int(branch_id)) | Q(existing_branch_id=int(branch_id)))



    rec_type = request.GET.get('record_type', '').strip()

    if rec_type:

        qs = qs.filter(record_type=rec_type)



    response = HttpResponse(content_type='text/csv; charset=utf-8')

    response['Content-Disposition'] = f'attachment; filename="duplicate_leads_export_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'



    writer = csv.writer(response)

    writer.writerow([

        'ID', 'Record Type', 'Student Name', 'Phone', 'Email',

        'Submitted Branch', 'Original Branch', 'Source', 'Action Taken',

        'Elapsed Days', 'Submitted At', 'Notes', 'Raw Payload JSON'

    ])



    for rec in qs:

        import json

        orig_branch = (rec.original_lead.branch.name if (rec.original_lead and rec.original_lead.branch)

                       else (rec.existing_branch_name or 'N/A'))

        dup_branch = rec.branch.name if rec.branch else (rec.branch_name or 'N/A')

        writer.writerow([

            rec.id,

            rec.get_record_type_display(),

            rec.name,

            rec.phone,

            rec.email,

            dup_branch,

            orig_branch,

            rec.source,

            rec.action_taken,

            rec.elapsed_days or '',

            timezone.localtime(rec.submitted_at).strftime('%Y-%m-%d %H:%M:%S'),

            rec.notes,

            json.dumps(rec.data_payload) if rec.data_payload else ''

        ])



    return response


@admin_required

def admin_duplicate_leads_view(request):

    """

    Renders the Duplicate Leads Dedicated Table Explorer page with full search,

    branch filtering, record type filtering, raw JSON payload inspection, and promotion.

    """

    qs = DuplicateLeadRecord.objects.exclude(record_type='ORIGINAL_INGESTION').select_related('original_lead', 'branch', 'original_lead__branch').order_by('-submitted_at')



    # Filter by Search Query

    search_q = request.GET.get('q', '').strip()

    if search_q:

        clean_p = re.sub(r'\D', '', search_q)

        target_10 = clean_p[-10:] if len(clean_p) >= 10 else clean_p

        search_filter = (

            Q(name__icontains=search_q) |

            Q(phone__icontains=search_q) |

            Q(email__icontains=search_q) |

            Q(source__icontains=search_q) |

            Q(duplicate_reason__icontains=search_q)

        )

        if target_10:

            search_filter |= Q(normalized_phone__icontains=target_10)

        qs = qs.filter(search_filter)



    # Filter by Branch

    branch_id = request.GET.get('branch_id', '').strip()

    if branch_id and branch_id.isdigit():

        qs = qs.filter(Q(branch_id=int(branch_id)) | Q(existing_branch_id=int(branch_id)))



    # Filter by Record Type

    rec_type = request.GET.get('record_type', '').strip()

    if rec_type:

        qs = qs.filter(record_type=rec_type)



    formatted_duplicates = []

    for rec in qs:

        orig = rec.original_lead

        if orig:

            orig_branch = orig.branch.name if orig.branch else (rec.existing_branch_name or 'N/A')

            orig_id = orig.id

            orig_url = reverse('admin_lead_detail', args=[orig.id])

            orig_date = timezone.localtime(orig.created_at).strftime('%d %b %Y, %I:%M %p') if orig.created_at else '—'

            lead_ids_str = f"{orig.id}"

            time_delta = rec.submitted_at - orig.created_at if orig.created_at else None

            diff_days = max(0.0, round(time_delta.total_seconds() / 86400.0, 1)) if time_delta else (rec.elapsed_days or 0.0)

        else:

            orig_branch = rec.existing_branch_name or 'Archived / N/A'

            orig_id = None

            orig_url = '#'

            orig_date = timezone.localtime(rec.existing_lead_created_at).strftime('%d %b %Y, %I:%M %p') if rec.existing_lead_created_at else '—'

            lead_ids_str = ""

            diff_days = rec.elapsed_days or 0.0



        dup_branch = rec.branch.name if rec.branch else (rec.branch_name or 'N/A')

        is_cross_branch_10day = (orig_branch != dup_branch and 'within 10 days' in (rec.notes or '').lower())

        diff_days_str = f"{int(diff_days)} days" if diff_days.is_integer() else f"{diff_days} days"



        status_label = rec.status or ('DUPLICATE' if diff_days <= 10.0 else 'New Submission (>10 Days)')



        formatted_duplicates.append({

            'id': rec.id,

            'name': rec.name,

            'phone': mask_phone(rec.phone),

            'raw_phone': rec.phone,

            'email': rec.email or '',

            'original_lead_id': orig_id,

            'original_lead_url': orig_url,

            'original_branch': orig_branch,

            'original_date': orig_date,

            'duplicate_branch': dup_branch,

            'duplicate_date': timezone.localtime(rec.submitted_at).strftime('%d %b %Y, %I:%M %p'),

            'days_difference': diff_days,

            'days_difference_display': diff_days_str,

            'status': status_label,

            'record_type': rec.record_type,

            'record_type_display': rec.get_record_type_display(),

            'source': rec.source,

            'action_taken': rec.action_taken,

            'notes': rec.notes,

            'is_cross_branch_10day': is_cross_branch_10day,

            'lead_ids_str': lead_ids_str,

            'has_payload': bool(rec.data_payload),

        })



    groups, total_groups_count = detect_all_duplicate_groups()

    all_branches = Branch.objects.filter(status='Active').order_by('name')



    return render(request, 'admin/duplicate_leads.html', {

        'duplicate_records': formatted_duplicates,

        'duplicate_groups': groups,

        'total_duplicate_count': len(formatted_duplicates),

        'total_groups_count': len(formatted_duplicates) if formatted_duplicates else total_groups_count,

        'all_branches': all_branches,

        'record_type_choices': DuplicateLeadRecord.RECORD_TYPE_CHOICES,

        'selected_search': search_q,

        'selected_branch': branch_id,

        'selected_type': rec_type,

    })


@admin_required

def admin_duplicate_lead_payload(request, rec_id):

    """

    Returns verbatim JSON payload and audit metadata for a duplicate record.

    """

    rec = get_object_or_404(DuplicateLeadRecord, id=rec_id)

    return JsonResponse({

        'success': True,

        'id': rec.id,

        'name': rec.name,

        'phone': rec.phone,

        'email': rec.email or '',

        'record_type': rec.get_record_type_display(),

        'source': rec.source,

        'branch': rec.branch_name or (rec.branch.name if rec.branch else 'N/A'),

        'existing_branch': rec.existing_branch_name or 'N/A',

        'submitted_at': timezone.localtime(rec.submitted_at).strftime('%d %b %Y, %I:%M %p'),

        'action_taken': rec.action_taken,

        'duplicate_reason': rec.duplicate_reason,

        'notes': rec.notes,

        'field_changes': rec.field_changes,

        'data_payload': rec.data_payload,

    })


@admin_required

def admin_duplicate_lead_promote(request, rec_id):

    """

    Promotes a duplicate entry into an independent lead (e.g. for siblings sharing a phone).

    """

    if request.method != 'POST':

        return JsonResponse({'success': False, 'error': 'POST method required.'}, status=405)



    rec = get_object_or_404(DuplicateLeadRecord, id=rec_id)

    from .assignment import assign_new_lead



    with transaction.atomic():

        new_lead = Lead.objects.create(

            name=rec.name,

            phone=rec.phone,

            email=rec.email or '',

            branch=rec.branch,

            source=rec.source or 'Promoted Duplicate',

            status=LeadStatus.NEW,

            notes=f"Promoted to independent lead from duplicate record #{rec.id} (Reason: {rec.duplicate_reason or 'Sibling/Family Contact'})."

        )

        rec.record_type = 'MANUAL_PROMOTED'

        rec.action_taken = 'MANUAL_PROMOTED'

        rec.notes = f"{rec.notes}\n[Promoted to separate Lead #{new_lead.id} on {timezone.now().strftime('%d %b %Y, %I:%M %p')}]"

        rec.save(update_fields=['record_type', 'action_taken', 'notes'])



        assign_new_lead(new_lead, branch=new_lead.branch, source=new_lead.source, triggered_by=request.user)



    msg = f"Successfully promoted '{new_lead.name}' ({new_lead.phone}) to independent Lead #{new_lead.id}!"

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':

        return JsonResponse({'success': True, 'message': msg, 'new_lead_id': new_lead.id})



    messages.success(request, msg)

    return redirect('admin_duplicate_leads')


@admin_required

def admin_duplicate_leads_keep_single(request):

    """

    Action to consolidate a duplicate group into a single unique lead record.

    Supports both AJAX POST and standard form POST.

    """

    if request.method != 'POST':

        return JsonResponse({'success': False, 'error': 'POST method required.'}, status=405)



    lead_ids_raw = request.POST.get('lead_ids', '').strip()

    if not lead_ids_raw:

        try:

            import json

            data = json.loads(request.body)

            lead_ids_raw = str(data.get('lead_ids', '')).strip()

        except Exception:

            pass



    if not lead_ids_raw:

        return JsonResponse({'success': False, 'error': 'No lead IDs provided.'}, status=400)



    try:

        primary_lead = keep_single_lead_for_group(lead_ids_raw, user=request.user)

        msg = f"Consolidated into single unique lead '{primary_lead.name}' ({primary_lead.phone}). Retained branches: {', '.join(primary_lead.get_all_branch_names())}."



        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':

            return JsonResponse({

                'success': True,

                'message': msg,

                'primary_id': primary_lead.id,

                'name': primary_lead.name,

                'phone': primary_lead.phone,

                'branches': primary_lead.get_all_branch_names(),

            })



        messages.success(request, msg)

        return redirect('admin_duplicate_leads')



    except Exception:

        logger.exception("Error consolidating duplicate leads")

        clean_msg = "Unable to consolidate these duplicate leads. Please try again."

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':

            return JsonResponse({'success': False, 'error': clean_msg}, status=400)

        messages.error(request, clean_msg)

        return redirect('admin_duplicate_leads')

