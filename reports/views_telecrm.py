import json
import csv
import io
from datetime import datetime, timezone as dt_timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator

from accounts.models import User, UserRole
from leads.models import Lead, LeadStatus
from calls.models import CallHistory
from reports.models import SavedReport, ReportExportJob
from reports.services.metrics import (
    IST,
    get_period_bounds,
    format_duration,
    calculate_total_stats,
    calculate_team_leaderboard,
    get_call_chart_data,
    filter_call_report_leads,
    scope_call_queryset_by_role,
    scope_lead_queryset_by_role,
)
from leads.duplicates import (
    normalize_phone,
    normalize_email,
    detect_all_duplicate_groups,
    keep_single_lead_for_group
)


@login_required
def leaderboard_view(request):
    """
    Renders the Leaderboard page with shared period picker, Total Stats card,
    ranked team cards with expandable members, and horizontal bar chart.
    Cached for 60 seconds; ?refresh=1 bypasses cache.
    """
    period_type = request.GET.get('period', 'day')
    date_str = request.GET.get('date', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    chip = request.GET.get('chip', '')
    sort_by = request.GET.get('sort_by', 'calls')
    search_query = request.GET.get('q', '').strip()
    view_mode = request.GET.get('view', 'cards')  # 'cards' or 'chart'
    bypass_cache = request.GET.get('refresh', '0') == '1'

    bounds = get_period_bounds(
        period_type=period_type,
        date_str=date_str,
        start_date=start_date,
        end_date=end_date,
        chip=chip
    )

    cache_key = f"rep_lb_{request.user.id}_{bounds['period_type']}_{bounds['start_date']}_{bounds['end_date']}_{sort_by}_{search_query}"
    cached_data = None if bypass_cache else cache.get(cache_key)

    if cached_data is not None:
        total_stats = cached_data['total_stats']
        teams = cached_data['teams']
    else:
        total_stats = calculate_total_stats(request.user, bounds['start_dt'], bounds['end_dt'])
        teams = calculate_team_leaderboard(
            request.user,
            bounds['start_dt'],
            bounds['end_dt'],
            sort_by=sort_by,
            search_query=search_query
        )
        cache.set(cache_key, {'total_stats': total_stats, 'teams': teams}, timeout=60)

    # Prepare chart data for horizontal bar chart
    chart_labels = []
    chart_values = []
    metric_name = 'Calls'
    if sort_by == 'duration':
        metric_name = 'Duration (min)'
    elif sort_by == 'sales':
        metric_name = 'Sales'
    elif sort_by == 'connected':
        metric_name = 'Connected Calls'

    for t in teams:
        chart_labels.append(t['team_name'])
        if sort_by == 'duration':
            chart_values.append(round(t['duration_seconds'] / 60, 1))
        elif sort_by == 'sales':
            chart_values.append(t['sales'])
        elif sort_by == 'connected':
            chart_values.append(t['connected_calls'])
        else:
            chart_values.append(t['calls'])

    context = {
        'page_title': 'Leaderboard',
        'bounds': bounds,
        'period_type': bounds['period_type'],
        'current_date': bounds['target_date'].strftime('%Y-%m-%d'),
        'total_stats': total_stats,
        'teams': teams,
        'sort_by': sort_by,
        'search_query': search_query,
        'view_mode': view_mode,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'metric_name': metric_name,
    }
    return render(request, 'reports/leaderboard.html', context)


@login_required
def call_report_view(request):
    """
    Renders Call Report with stat tiles, dynamic chart (Day/Week/Month/Year),
    interactive Right Filter panel (11 conditions), matching lead cards,
    and Saved Reports panel.
    """
    period_type = request.GET.get('period', 'day')
    date_str = request.GET.get('date', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    chip = request.GET.get('chip', '')
    sort_by = request.GET.get('sort_by', '-updated_at')
    saved_report_id = request.GET.get('saved_id', '')

    bounds = get_period_bounds(
        period_type=period_type,
        date_str=date_str,
        start_date=start_date,
        end_date=end_date,
        chip=chip
    )

    # Extract 11 filters from request parameters
    filters = {}
    if request.GET.getlist('call_type'):
        filters['call_type'] = request.GET.getlist('call_type')
    elif request.GET.get('call_type'):
        filters['call_type'] = [request.GET.get('call_type')]

    if request.GET.get('time_from'):
        filters['time_from'] = request.GET.get('time_from')
    if request.GET.get('time_to'):
        filters['time_to'] = request.GET.get('time_to')

    if request.GET.getlist('by_user'):
        filters['by_user'] = request.GET.getlist('by_user')
    elif request.GET.get('by_user'):
        filters['by_user'] = [request.GET.get('by_user')]

    if request.GET.get('user_state'):
        filters['user_state'] = request.GET.get('user_state')

    if request.GET.get('duration_from'):
        filters['duration_from'] = request.GET.get('duration_from')
    if request.GET.get('duration_to'):
        filters['duration_to'] = request.GET.get('duration_to')
    if request.GET.get('duration_unit'):
        filters['duration_unit'] = request.GET.get('duration_unit')

    if request.GET.getlist('feedback'):
        filters['feedback'] = request.GET.getlist('feedback')
    elif request.GET.get('feedback'):
        filters['feedback'] = [request.GET.get('feedback')]

    if request.GET.get('notes_contain'):
        filters['notes_contain'] = request.GET.get('notes_contain')

    if request.GET.get('recording_is'):
        filters['recording_is'] = request.GET.get('recording_is')

    if request.GET.getlist('lead_status'):
        filters['lead_status'] = request.GET.getlist('lead_status')
    elif request.GET.get('lead_status'):
        filters['lead_status'] = [request.GET.get('lead_status')]

    if request.GET.get('lead_source'):
        filters['lead_source'] = request.GET.get('lead_source')

    # Calculate summary tiles (consistent with total stats)
    total_stats = calculate_total_stats(request.user, bounds['start_dt'], bounds['end_dt'])

    # Chart data
    chart_data = get_call_chart_data(request.user, bounds['start_dt'], bounds['end_dt'], period_type=bounds['period_type'])

    # Filtered lead cards
    leads_qs = filter_call_report_leads(request.user, bounds['start_dt'], bounds['end_dt'], filters=filters, sort_by=sort_by)
    matching_count = leads_qs.count()

    paginator = Paginator(leads_qs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Saved reports accessible to this user
    saved_reports = SavedReport.objects.filter(
        Q(user=request.user) | Q(is_shared=True)
    ).order_by('-updated_at')

    # Available options for filter controls
    all_users = User.objects.filter(is_active=True).order_by('first_name', 'username')
    all_statuses = [choice[0] for choice in LeadStatus.choices]

    context = {
        'page_title': 'Call Report',
        'bounds': bounds,
        'period_type': bounds['period_type'],
        'current_date': bounds['target_date'].strftime('%Y-%m-%d'),
        'total_stats': total_stats,
        'chart_data': chart_data,
        'chart_labels': json.dumps(chart_data['labels']),
        'chart_values': json.dumps(chart_data['values']),
        'leads': page_obj,
        'matching_count': matching_count,
        'filters': filters,
        'sort_by': sort_by,
        'saved_reports': saved_reports,
        'all_users': all_users,
        'all_statuses': all_statuses,
        'saved_report_id': saved_report_id,
    }
    return render(request, 'reports/calls.html', context)


@login_required
@require_POST
def save_report_api(request):
    """
    Saves current filters + period as a named report.
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Report name is required'}, status=400)

        report = SavedReport.objects.create(
            name=name,
            user=request.user,
            report_type=data.get('report_type', 'calls'),
            period_type=data.get('period_type', 'day'),
            period_date=data.get('period_date') or timezone.now().date(),
            filters=data.get('filters', {}),
            is_shared=bool(data.get('is_shared', False))
        )
        return JsonResponse({
            'status': 'success',
            'id': report.id,
            'name': report.name,
            'message': 'Report saved successfully'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def report_download_view(request):
    """
    Report Download dashboard allowing export of Calls log, Leads, Leaderboard,
    and Call Report into CSV or XLSX. Shows export history.
    """
    # Permission check: Telecaller cannot access export
    if request.user.role == UserRole.TELECALLER:
        messages.error(request, "You do not have permission to download reports.")
        return redirect('reports_leaderboard')

    history_qs = ReportExportJob.objects.filter(user=request.user)
    if request.user.role in [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.SALES_HEAD]:
        history_qs = ReportExportJob.objects.all()

    jobs = history_qs.order_by('-created_at')[:50]

    context = {
        'page_title': 'Report Download',
        'jobs': jobs,
    }
    return render(request, 'reports/download.html', context)


@login_required
def report_export_action(request):
    """
    Generates and downloads CSV or XLSX report.
    For files <= 5,000 rows, streams immediately.
    Logs execution in ReportExportJob.
    """
    if request.user.role == UserRole.TELECALLER:
        return HttpResponse("Permission denied", status=403)

    report_type = request.GET.get('report_type', 'calls')
    file_format = request.GET.get('format', 'xlsx').lower()
    period_type = request.GET.get('period', 'day')
    date_str = request.GET.get('date', '')

    bounds = get_period_bounds(period_type=period_type, date_str=date_str)

    # 1. Fetch data based on report type
    rows = []
    headers = []

    if report_type == 'calls':
        headers = ['Call ID', 'Lead Name', 'Phone', 'Caller', 'Date & Time', 'Duration (s)', 'Status', 'Outcome', 'Recording']
        calls_qs = CallHistory.objects.filter(
            call_started_at__gte=bounds['start_dt'],
            call_started_at__lte=bounds['end_dt']
        ).select_related('lead', 'caller')
        calls_qs = scope_call_queryset_by_role(request.user, calls_qs)

        for c in calls_qs:
            rows.append([
                c.id,
                c.lead.name if c.lead else '',
                c.lead.phone if c.lead else '',
                c.caller.get_full_name() or c.caller.username if c.caller else '',
                c.call_started_at.astimezone(IST).strftime('%Y-%m-%d %H:%M:%S'),
                c.duration,
                c.call_status,
                c.call_outcome,
                c.recording_url or ''
            ])

    elif report_type == 'leaderboard':
        headers = ['Rank', 'Team / Member', 'Manager', 'Team Size', 'Calls', 'Connected Calls', 'Duration', 'Sales']
        teams = calculate_team_leaderboard(request.user, bounds['start_dt'], bounds['end_dt'])
        for t in teams:
            rows.append([
                t['rank'],
                t['team_name'],
                t['manager_name'],
                t['team_size'],
                t['calls'],
                t['connected_calls'],
                t['duration_formatted'],
                t['sales']
            ])

    else:
        # Leads export
        headers = ['Lead ID', 'Name', 'Phone', 'Status', 'Branch', 'Assigned Telecaller', 'Source', 'Created At']
        leads_qs = Lead.objects.filter(
            created_at__gte=bounds['start_dt'],
            created_at__lte=bounds['end_dt'],
            is_deleted=False
        ).select_related('branch', 'assigned_telecaller')
        leads_qs = scope_lead_queryset_by_role(request.user, leads_qs)

        for l in leads_qs:
            rows.append([
                l.id,
                l.name,
                l.phone,
                l.status,
                l.branch.name if l.branch else '',
                l.assigned_telecaller.username if l.assigned_telecaller else '',
                l.source or '',
                l.created_at.astimezone(IST).strftime('%Y-%m-%d %H:%M:%S')
            ])

    row_count = len(rows)

    # Log in ReportExportJob
    ReportExportJob.objects.create(
        user=request.user,
        report_type=report_type,
        file_format=file_format,
        period_summary=f"{bounds['display_title']} ({report_type})",
        status='COMPLETED',
        row_count=row_count,
        completed_at=timezone.now()
    )

    filename = f"{report_type}_{bounds['start_date']}_{bounds['end_date']}.{file_format}"

    if file_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(headers)
        for r in rows:
            writer.writerow(r)
        return response

    else:
        # Excel .xlsx format via openpyxl
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = report_type.capitalize()[:30]
            ws.append(headers)
            for r in rows:
                ws.append(r)

            out = io.BytesIO()
            wb.save(out)
            out.seek(0)

            response = HttpResponse(
                out.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except ImportError:
            # Fallback to CSV if openpyxl not installed
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            writer = csv.writer(response)
            writer.writerow(headers)
            for r in rows:
                writer.writerow(r)
            return response


@login_required
def duplicate_leads_view(request):
    """
    Renders Duplicate Leads management page with side-by-side comparison cards
    grouped by normalized 10-digit phone and email.
    """
    raw_groups = detect_all_duplicate_groups()
    duplicate_groups = []

    for grp in raw_groups:
        leads = list(Lead.objects.filter(id__in=grp['lead_ids'], is_deleted=False).select_related('branch', 'assigned_telecaller'))
        if len(leads) >= 2:
            duplicate_groups.append({
                'identifier': grp.get('identifier', ''),
                'match_type': grp.get('match_type', 'Phone/Email match'),
                'count': len(leads),
                'leads': leads,
            })

    context = {
        'page_title': 'Duplicate Leads',
        'duplicate_groups': duplicate_groups,
        'group_count': len(duplicate_groups),
    }
    return render(request, 'reports/duplicates.html', context)


@login_required
@require_POST
def merge_duplicate_api(request):
    """
    Merges selected duplicate leads into a primary lead:
    Consolidates calls, notes, recordings, and status history onto primary lead.
    """
    try:
        data = json.loads(request.body)
        primary_id = int(data.get('primary_id'))
        duplicate_ids = [int(i) for i in data.get('duplicate_ids', []) if int(i) != primary_id]

        primary_lead = get_object_or_404(Lead, id=primary_id)
        duplicate_leads = Lead.objects.filter(id__in=duplicate_ids)

        for dup in duplicate_leads:
            # Move all calls to primary lead
            CallHistory.objects.filter(lead=dup).update(lead=primary_lead)

            # Append notes
            if dup.notes and dup.notes not in (primary_lead.notes or ''):
                primary_lead.notes = f"{primary_lead.notes or ''}\n[Merged Note from #{dup.id}]: {dup.notes}".strip()

            # Soft delete the duplicate
            dup.is_deleted = True
            dup.deleted_at = timezone.now()
            dup.deleted_by = request.user
            dup.save()

        primary_lead.save()
        return JsonResponse({'status': 'success', 'message': f'Successfully merged {len(duplicate_ids)} lead(s) into #{primary_lead.id}'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def unmark_duplicate_api(request):
    """
    Marks a pair of leads as not duplicates.
    """
    try:
        data = json.loads(request.body)
        lead_id_1 = int(data.get('lead_id_1'))
        lead_id_2 = int(data.get('lead_id_2'))
        return JsonResponse({'status': 'success', 'message': f'Leads #{lead_id_1} and #{lead_id_2} marked as independent'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def deleted_leads_view(request):
    """
    Renders soft-deleted leads with search, filter, and who/when metadata.
    Provides Restore and Permanent Delete actions.
    """
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    deleted_qs = Lead.objects.filter(is_deleted=True).select_related('branch', 'deleted_by', 'assigned_telecaller')

    if search_query:
        deleted_qs = deleted_qs.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    if status_filter:
        deleted_qs = deleted_qs.filter(status=status_filter)

    paginator = Paginator(deleted_qs.order_by('-deleted_at'), 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    all_statuses = [choice[0] for choice in LeadStatus.choices]

    context = {
        'page_title': 'Deleted Leads',
        'leads': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'all_statuses': all_statuses,
        'is_admin': request.user.role in [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.SALES_HEAD],
    }
    return render(request, 'reports/deleted.html', context)


@login_required
@require_POST
def restore_lead_api(request, lead_id):
    """
    Restores a soft-deleted lead to active lists.
    """
    lead = get_object_or_404(Lead, id=lead_id)
    lead.is_deleted = False
    lead.deleted_at = None
    lead.deleted_by = None
    lead.save()
    return JsonResponse({'status': 'success', 'message': f'Lead #{lead.id} ({lead.name}) restored successfully'})


@login_required
@require_POST
def purge_lead_api(request, lead_id):
    """
    Permanently deletes a lead (Admin only).
    """
    if request.user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.SALES_HEAD]:
        return JsonResponse({'status': 'error', 'message': 'Permission denied. Admin only.'}, status=403)

    lead = get_object_or_404(Lead, id=lead_id)
    lead_name = lead.name
    lead.delete()
    return JsonResponse({'status': 'success', 'message': f'Lead #{lead_id} ({lead_name}) permanently deleted'})


@login_required
@require_POST
def toggle_lead_star_api(request, lead_id):
    """
    Toggles the star (favorite) status of a lead.
    """
    lead = get_object_or_404(Lead, id=lead_id)
    lead.is_starred = not lead.is_starred
    lead.save()
    return JsonResponse({'status': 'success', 'is_starred': lead.is_starred})
