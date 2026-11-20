from datetime import datetime, time, timedelta
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET

from accounts.permissions import marketing_required
from accounts.models import User, UserRole
from leads.models import Lead, LeadStatus
from branches.models import Branch
from lead_channels.models import Channel
from products.models import Product
from followups.models import FollowUp
from calls.models import CallHistory
from activities.models import Activity
from leads.views import _apply_telecrm_dynamic_filters, _get_safe_saved_views
from leads.utils import get_validated_page_size


@marketing_required
def marketing_dashboard(request):
    """
    Marketing Team Executive Dashboard.
    Provides comprehensive lead acquisition metrics, source breakdowns,
    campaign attribution, and branch performance across all branches.
    """
    now = timezone.now()
    today_start = timezone.make_aware(datetime.combine(now.date(), time.min))
    week_start = today_start - timedelta(days=7)
    month_start = today_start.replace(day=1)

    all_leads = Lead.objects.all()
    total_leads = all_leads.count()

    converted_statuses = [LeadStatus.CONVERTED, LeadStatus.JOINED, 'Enrolled']
    converted_leads = all_leads.filter(status__in=converted_statuses).count()
    conversion_rate = round((converted_leads / total_leads * 100), 1) if total_leads > 0 else 0.0

    new_leads_count = all_leads.filter(status=LeadStatus.NEW).count()
    today_leads = all_leads.filter(created_at__gte=today_start).count()
    week_leads = all_leads.filter(created_at__gte=week_start).count()
    month_leads = all_leads.filter(created_at__gte=month_start).count()

    # Source performance breakdown
    source_aggregates = all_leads.values('source').annotate(
        total=Count('id'),
        converted=Count('id', filter=Q(status__in=converted_statuses))
    ).order_by('-total')[:10]

    source_stats = []
    for item in source_aggregates:
        src_name = item['source'] or 'Direct / Unspecified'
        cnt = item['total']
        conv = item['converted']
        rate = round((conv / cnt * 100), 1) if cnt > 0 else 0.0
        pct_of_total = round((cnt / total_leads * 100), 1) if total_leads > 0 else 0.0
        source_stats.append({
            'source': src_name,
            'total': cnt,
            'converted': conv,
            'rate': rate,
            'pct_of_total': pct_of_total,
        })

    # Channel performance breakdown
    channel_aggregates = all_leads.values('channel__name').annotate(
        total=Count('id'),
        converted=Count('id', filter=Q(status__in=converted_statuses))
    ).order_by('-total')[:8]

    channel_stats = []
    for item in channel_aggregates:
        ch_name = item['channel__name'] or 'Direct Channel'
        cnt = item['total']
        conv = item['converted']
        rate = round((conv / cnt * 100), 1) if cnt > 0 else 0.0
        channel_stats.append({
            'channel': ch_name,
            'total': cnt,
            'converted': conv,
            'rate': rate,
        })

    # Branch distribution breakdown
    branch_aggregates = all_leads.values('branch__name').annotate(
        total=Count('id'),
        converted=Count('id', filter=Q(status__in=converted_statuses))
    ).order_by('-total')

    branch_stats = []
    for item in branch_aggregates:
        b_name = item['branch__name'] or 'Central / Unassigned'
        cnt = item['total']
        conv = item['converted']
        rate = round((conv / cnt * 100), 1) if cnt > 0 else 0.0
        branch_stats.append({
            'branch': b_name,
            'total': cnt,
            'converted': conv,
            'rate': rate,
        })

    # Recent incoming leads stream
    recent_leads = all_leads.select_related(
        'branch', 'channel', 'product', 'assigned_telecaller', 'assigned_counselor'
    ).order_by('-created_at')[:10]

    context = {
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'conversion_rate': conversion_rate,
        'new_leads_count': new_leads_count,
        'today_leads': today_leads,
        'week_leads': week_leads,
        'month_leads': month_leads,
        'source_stats': source_stats,
        'channel_stats': channel_stats,
        'branch_stats': branch_stats,
        'recent_leads': recent_leads,
        'is_marketing_user': True,
    }
    return render(request, 'marketing/dashboard.html', context)


@marketing_required
def marketing_leads_list(request):
    """
    Full view of all leads across all branches with full TeleCRM visual filter builder.
    Strictly read-only: no edits, reassignments, or deletions permitted.
    """
    active_view = request.GET.get('view', 'all').strip()
    rating_filter = request.GET.get('rating', '').strip()
    search_query = request.GET.get('search', '').strip()
    global_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    channel_filter = request.GET.get('channel', '').strip()
    product_filter = request.GET.get('product', '').strip()
    branch_filter = request.GET.get('branch', '').strip()
    source_filter = request.GET.get('source', '').strip()
    date_from = (request.GET.get('date_from') or request.GET.get('from_date') or '').strip()
    date_to = (request.GET.get('date_to') or request.GET.get('to_date') or '').strip()
    sort_by = request.GET.get('sort', '-created_at').strip()

    leads_qs = Lead.objects.all().select_related(
        'channel', 'product', 'branch', 'assigned_sales_head', 'assigned_telecaller', 'assigned_counselor'
    ).prefetch_related('duplicate_records', 'calls', 'followups')

    # View presets
    if active_view == 'all_active':
        leads_qs = leads_qs.exclude(status__in=[LeadStatus.LOST, LeadStatus.CONVERTED])
    elif active_view == 'new':
        leads_qs = leads_qs.filter(status=LeadStatus.NEW)
    elif active_view == 'converted':
        leads_qs = leads_qs.filter(status__in=[LeadStatus.CONVERTED, LeadStatus.JOINED, 'Enrolled'])

    # Global search query (across name, phone, email, notes)
    if global_query:
        leads_qs = leads_qs.filter(
            Q(name__icontains=global_query) |
            Q(phone__icontains=global_query) |
            Q(email__icontains=global_query) |
            Q(notes__icontains=global_query)
        )

    # Rating filter
    if rating_filter:
        try:
            leads_qs = leads_qs.filter(rating=int(rating_filter))
        except (ValueError, TypeError):
            pass

    # Status filter
    if status_filter:
        if status_filter.lower() == 'active':
            leads_qs = leads_qs.exclude(status__in=[LeadStatus.LOST, LeadStatus.CONVERTED])
        else:
            leads_qs = leads_qs.filter(status=status_filter)

    # Branch filter
    if branch_filter:
        leads_qs = leads_qs.filter(branch_id=branch_filter)

    # Source filter
    if source_filter:
        leads_qs = leads_qs.filter(Q(source__icontains=source_filter) | Q(channel__name__icontains=source_filter))

    # Channel filter
    if channel_filter:
        if channel_filter.isdigit():
            leads_qs = leads_qs.filter(channel_id=int(channel_filter))
        else:
            leads_qs = leads_qs.filter(Q(channel__name__icontains=channel_filter) | Q(source__icontains=channel_filter))

    # Product / Course filter
    if product_filter:
        leads_qs = leads_qs.filter(product_id=product_filter)

    # Date range filters
    if date_from:
        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            dt_from = timezone.make_aware(datetime.combine(d_from, time.min))
            leads_qs = leads_qs.filter(created_at__gte=dt_from)
        except (ValueError, TypeError):
            pass

    if date_to:
        try:
            d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            dt_to = timezone.make_aware(datetime.combine(d_to, time.max))
            leads_qs = leads_qs.filter(created_at__lte=dt_to)
        except (ValueError, TypeError):
            pass

    # Dynamic TeleCRM filter builder parameters & condition operators
    leads_qs, telecrm_filter_ctx = _apply_telecrm_dynamic_filters(leads_qs, request)

    # Sorting
    allowed_sorts = ['name', '-name', 'created_at', '-created_at', 'updated_at', '-updated_at', 'status', '-status', 'rating', '-rating']
    if sort_by in allowed_sorts:
        leads_qs = leads_qs.order_by(sort_by, '-id')
    else:
        leads_qs = leads_qs.order_by('-created_at', '-id')

    # Total counts
    total_leads_count = leads_qs.count()

    # Pagination
    page_size = get_validated_page_size(request, default=20)
    paginator = Paginator(leads_qs, page_size)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Metadata for filter selects
    branches = Branch.objects.filter(status='Active').order_by('name')
    channels = Channel.objects.filter(status='Active').order_by('name')
    products = Product.objects.filter(status='Active').order_by('name')
    statuses = LeadStatus.choices
    telecallers = User.objects.filter(role=UserRole.TELECALLER, is_active=True).order_by('first_name', 'username')

    saved_views = _get_safe_saved_views(request)

    view_counts = {
        'all': Lead.objects.count(),
        'all_active': Lead.objects.exclude(status__in=[LeadStatus.LOST, LeadStatus.CONVERTED]).count(),
        'new': Lead.objects.filter(status=LeadStatus.NEW).count(),
        'converted': Lead.objects.filter(status__in=[LeadStatus.CONVERTED, LeadStatus.JOINED, 'Enrolled']).count(),
    }

    context = {
        'leads': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_leads_count': total_leads_count,
        'active_view': active_view,
        'view_counts': view_counts,
        'saved_views': saved_views,
        'branches': branches,
        'channels': channels,
        'products': products,
        'statuses': statuses,
        'telecallers': telecallers,
        'rating_filter': rating_filter,
        'search_query': search_query,
        'status_filter': status_filter,
        'channel_filter': channel_filter,
        'product_filter': product_filter,
        'branch_filter': branch_filter,
        'source_filter': source_filter,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
        'page_size': page_size,
        'is_marketing_readonly': True,
        'is_marketing_user': True,
        'form_action_url': 'marketing_leads_list',
        'lead_detail_url_name': 'marketing_lead_detail',
    }
    context.update(telecrm_filter_ctx)
    return render(request, 'admin/leads_list.html', context)


@marketing_required
def marketing_lead_detail(request, pk):
    """
    Read-only lead detail profile for Marketing Team.
    Displays complete lead fields, campaign attribution, timeline, and history without modification controls.
    """
    lead = get_object_or_404(
        Lead.objects.select_related(
            'channel', 'product', 'branch', 'assigned_sales_head', 'assigned_telecaller', 'assigned_counselor'
        ),
        pk=pk
    )

    followups = FollowUp.objects.filter(lead=lead).order_by('-created_at')
    calls = CallHistory.objects.filter(lead=lead).select_related('caller').order_by('-call_started_at')
    activities = Activity.objects.filter(object_type='Lead', object_id=str(lead.pk)).order_by('-timestamp')
    call_recordings = lead.drive_recordings.all().select_related('drive_connection').order_by('-recording_date', '-created_at')
    status_history = lead.status_history.select_related('changed_by').order_by('-created_at')[:25]

    from leads.detail_service import build_lead_detail_context
    context = build_lead_detail_context(lead, request.user)
    context.update({
        'lead': lead,
        'followups': followups,
        'calls': calls,
        'activities': activities,
        'call_recordings': call_recordings,
        'status_history': status_history,
        'timeline_count': (len(calls) if calls else 0) + (len(status_history) if status_history else 0) + (len(followups) if followups else 0) + (len(activities) if activities else 0),
        'detail_url_name': 'marketing_lead_detail',
        'edit_url_name': None,
        'list_url_name': 'marketing_leads_list',
        'is_marketing_readonly': True,
        'is_marketing_user': True,
    })
    return render(request, 'leads/lead_detail_view.html', context)


@marketing_required
def marketing_export_leads(request):
    """
    Export filtered leads to CSV for marketing analysis.
    """
    leads_qs = Lead.objects.all().select_related('channel', 'branch', 'product')

    search_query = request.GET.get('search', '').strip()
    if search_query:
        leads_qs = leads_qs.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    branch_filter = request.GET.get('branch', '').strip()
    if branch_filter:
        leads_qs = leads_qs.filter(branch_id=branch_filter)

    source_filter = request.GET.get('source', '').strip()
    if source_filter:
        leads_qs = leads_qs.filter(Q(source__icontains=source_filter) | Q(channel__name__icontains=source_filter))

    channel_filter = request.GET.get('channel', '').strip()
    if channel_filter:
        if channel_filter.isdigit():
            leads_qs = leads_qs.filter(channel_id=int(channel_filter))
        else:
            leads_qs = leads_qs.filter(Q(channel__name__icontains=channel_filter) | Q(source__icontains=channel_filter))

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        leads_qs = leads_qs.filter(status=status_filter)

    # Dynamic TeleCRM filter conditions
    leads_qs, _ = _apply_telecrm_dynamic_filters(leads_qs, request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="marketing_leads_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Lead ID', 'Name', 'Phone', 'Email', 'Status', 'Branch',
        'Source', 'Channel', 'Course / Product', 'Rating', 'Created At'
    ])

    for ld in leads_qs.order_by('-created_at')[:5000]:
        writer.writerow([
            ld.pk,
            ld.name,
            ld.phone,
            ld.email or '',
            ld.status or '',
            ld.branch.name if ld.branch else 'Unassigned',
            ld.source or '',
            ld.channel.name if ld.channel else '',
            ld.product.name if ld.product else '',
            ld.rating or 0,
            ld.created_at.strftime('%Y-%m-%d %H:%M:%S') if ld.created_at else ''
        ])

    return response
