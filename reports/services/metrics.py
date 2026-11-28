import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from django.conf import settings

from accounts.models import User, UserRole
from branches.models import Branch
from calls.models import CallHistory, CallStatus, CallOutcome
from leads.models import Lead, LeadStatus

logger = logging.getLogger('crm')

IST = ZoneInfo('Asia/Kolkata')
DEFAULT_WON_STATUSES = getattr(settings, 'REPORTS_WON_STATUSES', ['Converted', 'Enrolled', 'Joined'])


def format_duration(seconds):
    """
    Format duration in seconds to standard representation:
    e.g. 5400s -> '1:30h', 900s -> '15m', 0s -> '0s'
    """
    if not seconds or seconds <= 0:
        return '0s'
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    rem_seconds = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}h"
    elif minutes > 0:
        return f"{minutes}m"
    return f"{rem_seconds}s"


def get_period_bounds(period_type='day', date_str=None, start_date=None, end_date=None, chip=None):
    """
    Computes exact start and end datetime bounds in Asia/Kolkata (IST).
    A day spans 00:00:00 to 23:59:59.999999 IST.
    """
    now_ist = timezone.now().astimezone(IST)
    today = now_ist.date()

    if chip:
        chip_lower = chip.lower().replace(' ', '_')
        if chip_lower == 'today':
            period_type = 'day'
            target_date = today
        elif chip_lower == 'yesterday':
            period_type = 'day'
            target_date = today - timedelta(days=1)
        elif chip_lower == 'this_week':
            period_type = 'week'
            target_date = today
        elif chip_lower == 'last_week':
            period_type = 'week'
            target_date = today - timedelta(days=7)
        elif chip_lower == 'this_month':
            period_type = 'month'
            target_date = today
        elif chip_lower == 'last_month':
            period_type = 'month'
            # First day of this month minus 1 day is in last month
            first_this_month = today.replace(day=1)
            target_date = first_this_month - timedelta(days=1)
        elif chip_lower == 'this_year':
            period_type = 'year'
            target_date = today
        elif chip_lower == 'custom' and (start_date or date_str):
            target_date = today
        else:
            target_date = today
    else:
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                target_date = today
        else:
            target_date = today

    period_type = period_type.lower()
    if period_type == 'week':
        # Monday to Sunday
        start_date_calc = target_date - timedelta(days=target_date.weekday())
        end_date_calc = start_date_calc + timedelta(days=6)
        display_title = f"{start_date_calc.strftime('%d %b')} - {end_date_calc.strftime('%d %b %Y')}"
        prev_date = (start_date_calc - timedelta(days=7)).strftime('%Y-%m-%d')
        next_date = (start_date_calc + timedelta(days=7)).strftime('%Y-%m-%d')
    elif period_type == 'month':
        start_date_calc = target_date.replace(day=1)
        # Next month first day minus 1 day
        next_month = (start_date_calc.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_date_calc = next_month - timedelta(days=1)
        display_title = start_date_calc.strftime('%B %Y')
        prev_date = (start_date_calc - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d')
        next_date = next_month.strftime('%Y-%m-%d')
    elif period_type == 'year':
        start_date_calc = target_date.replace(month=1, day=1)
        end_date_calc = target_date.replace(month=12, day=31)
        display_title = str(target_date.year)
        prev_date = target_date.replace(year=target_date.year - 1).strftime('%Y-%m-%d')
        next_date = target_date.replace(year=target_date.year + 1).strftime('%Y-%m-%d')
    elif period_type == 'custom' and start_date and end_date:
        try:
            start_date_calc = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_calc = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            start_date_calc = target_date
            end_date_calc = target_date
        display_title = f"{start_date_calc.strftime('%d %b %Y')} - {end_date_calc.strftime('%d %b %Y')}"
        prev_date = (start_date_calc - (end_date_calc - start_date_calc + timedelta(days=1))).strftime('%Y-%m-%d')
        next_date = (end_date_calc + timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        # Default: DAY
        period_type = 'day'
        start_date_calc = target_date
        end_date_calc = target_date
        if target_date == today:
            display_title = f"Today, {target_date.strftime('%d %b %Y')}"
        elif target_date == today - timedelta(days=1):
            display_title = f"Yesterday, {target_date.strftime('%d %b %Y')}"
        else:
            display_title = target_date.strftime('%d %b %Y')
        prev_date = (target_date - timedelta(days=1)).strftime('%Y-%m-%d')
        next_date = (target_date + timedelta(days=1)).strftime('%Y-%m-%d')

    start_dt = datetime.combine(start_date_calc, time.min, tzinfo=IST)
    end_dt = datetime.combine(end_date_calc, time.max, tzinfo=IST)

    return {
        'start_dt': start_dt,
        'end_dt': end_dt,
        'start_date': start_date_calc,
        'end_date': end_date_calc,
        'period_type': period_type,
        'target_date': target_date,
        'display_title': display_title,
        'prev_date': prev_date,
        'next_date': next_date,
        'chip': chip or ('Today' if target_date == today else 'Custom')
    }


def scope_call_queryset_by_role(user, qs):
    """
    Apply role permissions to CallHistory querysets:
    - Superadmin / Admin / Sales Head: Full view
    - Branch Head: Calls within branch
    - Counselor: Calls by self or assigned telecallers
    - Telecaller: Own calls only
    """
    if not user or not user.is_authenticated:
        return qs.none()

    role = getattr(user, 'role', '')
    if role in [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.SALES_HEAD]:
        return qs

    if role in [UserRole.BRANCH_HEAD, UserRole.BRANCH_ADMIN]:
        if user.branch:
            return qs.filter(Q(caller__branch=user.branch) | Q(lead__branch=user.branch))
        return qs.none()

    if role == UserRole.COUNSELOR:
        team_user_ids = list(user.assigned_telecallers.values_list('id', flat=True)) + [user.id]
        return qs.filter(caller_id__in=team_user_ids)

    if role == UserRole.TELECALLER:
        return qs.filter(caller=user)

    return qs.filter(caller=user)


def scope_lead_queryset_by_role(user, qs, include_deleted=False):
    """
    Apply role permissions to Lead querysets and enforce soft delete filtering:
    - Superadmin / Admin / Sales Head: All leads
    - Branch Head: Own branch leads
    - Counselor: Assigned counselor or assigned to team telecaller
    - Telecaller: Own assigned leads
    """
    if not user or not user.is_authenticated:
        return qs.none()

    if not include_deleted:
        qs = qs.filter(is_deleted=False)

    role = getattr(user, 'role', '')
    if role in [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.SALES_HEAD]:
        return qs

    if role in [UserRole.BRANCH_HEAD, UserRole.BRANCH_ADMIN]:
        if user.branch:
            return qs.filter(branch=user.branch)
        return qs.none()

    if role == UserRole.COUNSELOR:
        team_user_ids = list(user.assigned_telecallers.values_list('id', flat=True))
        return qs.filter(Q(assigned_counselor=user) | Q(assigned_telecaller_id__in=team_user_ids))

    if role == UserRole.TELECALLER:
        return qs.filter(assigned_telecaller=user)

    return qs.filter(assigned_telecaller=user)


def calculate_total_stats(user, start_dt, end_dt):
    """
    Single source of truth for total call and sales statistics for a given period.
    """
    calls_qs = CallHistory.objects.filter(
        call_started_at__gte=start_dt,
        call_started_at__lte=end_dt
    )
    calls_qs = scope_call_queryset_by_role(user, calls_qs)

    agg = calls_qs.aggregate(
        total_calls=Count('id'),
        connected_calls=Count('id', filter=Q(duration__gt=0)),
        total_duration=Sum('duration')
    )

    total_calls = agg['total_calls'] or 0
    connected_calls = agg['connected_calls'] or 0
    duration_seconds = agg['total_duration'] or 0

    avg_seconds = (duration_seconds // connected_calls) if connected_calls > 0 else 0

    # Sales metric: leads converted/enrolled during this period
    leads_qs = Lead.objects.filter(
        status__in=DEFAULT_WON_STATUSES,
        updated_at__gte=start_dt,
        updated_at__lte=end_dt
    )
    leads_qs = scope_lead_queryset_by_role(user, leads_qs)
    sales_count = leads_qs.count()

    # Team size: active staff scoped by role
    user_qs = User.objects.filter(is_active=True)
    role = getattr(user, 'role', '')
    if role in [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.SALES_HEAD]:
        team_size = user_qs.filter(role__in=[UserRole.TELECALLER, UserRole.COUNSELOR]).count()
    elif role in [UserRole.BRANCH_HEAD, UserRole.BRANCH_ADMIN]:
        team_size = user_qs.filter(branch=user.branch, role__in=[UserRole.TELECALLER, UserRole.COUNSELOR]).count()
    elif role == UserRole.COUNSELOR:
        team_size = user.assigned_telecallers.filter(is_active=True).count()
    else:
        team_size = 1

    return {
        'calls': total_calls,
        'connected_calls': connected_calls,
        'duration_seconds': duration_seconds,
        'duration_formatted': format_duration(duration_seconds),
        'avg_duration_formatted': format_duration(avg_seconds),
        'sales': sales_count,
        'team_size': team_size
    }


def calculate_team_leaderboard(user, start_dt, end_dt, sort_by='calls', search_query=''):
    """
    Ranks teams by the chosen metric: 'calls', 'duration', 'sales', 'connected'.
    Groups users by manager (Counselor). Unassigned users go into an 'Unassigned' team card.
    Team totals + Unassigned totals strictly reconcile with calculate_total_stats.
    """
    # 1. Base call query in period scoped by user
    calls_base = CallHistory.objects.filter(
        call_started_at__gte=start_dt,
        call_started_at__lte=end_dt
    )
    calls_base = scope_call_queryset_by_role(user, calls_base)

    # 2. Per-user aggregates
    user_call_aggs = calls_base.values('caller_id').annotate(
        calls=Count('id'),
        connected_calls=Count('id', filter=Q(duration__gt=0)),
        duration=Sum('duration')
    )
    user_call_map = {item['caller_id']: item for item in user_call_aggs if item['caller_id']}

    # 3. Per-user sales in period
    won_leads = Lead.objects.filter(
        status__in=DEFAULT_WON_STATUSES,
        updated_at__gte=start_dt,
        updated_at__lte=end_dt
    )
    won_leads = scope_lead_queryset_by_role(user, won_leads)
    user_sales_aggs = won_leads.values('assigned_telecaller_id').annotate(sales=Count('id'))
    user_sales_map = {item['assigned_telecaller_id']: item['sales'] for item in user_sales_aggs if item['assigned_telecaller_id']}

    # 4. Resolve teams
    # A team is defined as a manager (Counselor/Branch Head) with assigned telecallers
    managers_qs = User.objects.filter(is_active=True).filter(
        Q(role=UserRole.COUNSELOR) | Q(assigned_telecallers__isnull=False)
    ).distinct()

    role = getattr(user, 'role', '')
    if role in [UserRole.BRANCH_HEAD, UserRole.BRANCH_ADMIN] and user.branch:
        managers_qs = managers_qs.filter(branch=user.branch)
    elif role == UserRole.COUNSELOR:
        managers_qs = managers_qs.filter(id=user.id)
    elif role == UserRole.TELECALLER:
        if user.counselor:
            managers_qs = managers_qs.filter(id=user.counselor_id)
        else:
            managers_qs = managers_qs.none()

    teams = []
    accounted_user_ids = set()

    for mgr in managers_qs:
        assigned_tcs = list(mgr.assigned_telecallers.filter(is_active=True))
        member_users = assigned_tcs + ([mgr] if mgr.role != UserRole.COUNSELOR or True else [])
        accounted_user_ids.add(mgr.id)
        for tc in assigned_tcs:
            accounted_user_ids.add(tc.id)

        team_calls = 0
        team_connected = 0
        team_duration = 0
        team_sales = 0
        members_data = []

        for u in member_users:
            u_stat = user_call_map.get(u.id, {'calls': 0, 'connected_calls': 0, 'duration': 0})
            u_sales = user_sales_map.get(u.id, 0)
            u_duration = u_stat['duration'] or 0
            u_conn = u_stat['connected_calls'] or 0
            u_avg = (u_duration // u_conn) if u_conn > 0 else 0

            team_calls += u_stat['calls']
            team_connected += u_conn
            team_duration += u_duration
            team_sales += u_sales

            members_data.append({
                'id': u.id,
                'name': u.get_full_name() or u.username,
                'username': u.username,
                'role': u.get_role_display(),
                'calls': u_stat['calls'],
                'connected_calls': u_conn,
                'duration_seconds': u_duration,
                'duration_formatted': format_duration(u_duration),
                'avg_duration_formatted': format_duration(u_avg),
                'sales': u_sales
            })

        # Sort members by chosen metric
        if sort_by == 'duration':
            members_data.sort(key=lambda m: m['duration_seconds'], reverse=True)
        elif sort_by == 'sales':
            members_data.sort(key=lambda m: m['sales'], reverse=True)
        elif sort_by == 'connected':
            members_data.sort(key=lambda m: m['connected_calls'], reverse=True)
        else:
            members_data.sort(key=lambda m: m['calls'], reverse=True)

        team_avg = (team_duration // team_connected) if team_connected > 0 else 0

        teams.append({
            'is_unassigned': False,
            'manager_id': mgr.id,
            'manager_name': mgr.get_full_name() or mgr.username,
            'team_name': f"{mgr.first_name or mgr.username}'s Team",
            'team_size': len(assigned_tcs) or 1,
            'calls': team_calls,
            'connected_calls': team_connected,
            'duration_seconds': team_duration,
            'duration_formatted': format_duration(team_duration),
            'avg_duration_formatted': format_duration(team_avg),
            'sales': team_sales,
            'members': members_data
        })

    # 5. Build Unassigned Team Card for users with calls/leads who are not in any team
    all_active_caller_ids = set(user_call_map.keys()) | set(user_sales_map.keys())
    unassigned_ids = all_active_caller_ids - accounted_user_ids

    if unassigned_ids:
        unassigned_users = User.objects.filter(id__in=unassigned_ids)
        un_calls = 0
        un_connected = 0
        un_duration = 0
        un_sales = 0
        un_members = []

        for u in unassigned_users:
            u_stat = user_call_map.get(u.id, {'calls': 0, 'connected_calls': 0, 'duration': 0})
            u_sales = user_sales_map.get(u.id, 0)
            u_duration = u_stat['duration'] or 0
            u_conn = u_stat['connected_calls'] or 0
            u_avg = (u_duration // u_conn) if u_conn > 0 else 0

            un_calls += u_stat['calls']
            un_connected += u_conn
            un_duration += u_duration
            un_sales += u_sales

            un_members.append({
                'id': u.id,
                'name': u.get_full_name() or u.username,
                'username': u.username,
                'role': u.get_role_display(),
                'calls': u_stat['calls'],
                'connected_calls': u_conn,
                'duration_seconds': u_duration,
                'duration_formatted': format_duration(u_duration),
                'avg_duration_formatted': format_duration(u_avg),
                'sales': u_sales
            })

        if sort_by == 'duration':
            un_members.sort(key=lambda m: m['duration_seconds'], reverse=True)
        elif sort_by == 'sales':
            un_members.sort(key=lambda m: m['sales'], reverse=True)
        elif sort_by == 'connected':
            un_members.sort(key=lambda m: m['connected_calls'], reverse=True)
        else:
            un_members.sort(key=lambda m: m['calls'], reverse=True)

        un_avg = (un_duration // un_connected) if un_connected > 0 else 0

        teams.append({
            'is_unassigned': True,
            'manager_id': None,
            'manager_name': 'Unassigned',
            'team_name': 'Unassigned / Direct',
            'team_size': len(un_members),
            'calls': un_calls,
            'connected_calls': un_connected,
            'duration_seconds': un_duration,
            'duration_formatted': format_duration(un_duration),
            'avg_duration_formatted': format_duration(un_avg),
            'sales': un_sales,
            'members': un_members
        })

    # 6. Sort teams by chosen metric
    if sort_by == 'duration':
        teams.sort(key=lambda t: (not t['is_unassigned'], t['duration_seconds']), reverse=True)
    elif sort_by == 'sales':
        teams.sort(key=lambda t: (not t['is_unassigned'], t['sales']), reverse=True)
    elif sort_by == 'connected':
        teams.sort(key=lambda t: (not t['is_unassigned'], t['connected_calls']), reverse=True)
    else:
        teams.sort(key=lambda t: (not t['is_unassigned'], t['calls']), reverse=True)

    # 7. Assign ranks #1, #2...
    rank = 1
    for t in teams:
        if not t['is_unassigned']:
            t['rank'] = rank
            rank += 1
        else:
            t['rank'] = '-'

    # 8. Filter by search query if provided
    if search_query:
        sq = search_query.strip().lower()
        filtered_teams = []
        for t in teams:
            team_match = sq in t['team_name'].lower() or sq in t['manager_name'].lower()
            matching_members = [m for m in t['members'] if sq in m['name'].lower() or sq in m['username'].lower()]
            if team_match or matching_members:
                t_copy = dict(t)
                if not team_match and matching_members:
                    t_copy['members'] = matching_members
                filtered_teams.append(t_copy)
        teams = filtered_teams

    return teams


def get_call_chart_data(user, start_dt, end_dt, period_type='day'):
    """
    Builds aggregated chart bars matching reference:
    - DAY: 24 bars (00:00 - 23:00) with call counts
    - WEEK: 7 bars (Mon - Sun)
    - MONTH: Daily bars for the month
    - YEAR: 12 bars (Jan - Dec)
    """
    calls_qs = CallHistory.objects.filter(
        call_started_at__gte=start_dt,
        call_started_at__lte=end_dt
    )
    calls_qs = scope_call_queryset_by_role(user, calls_qs)

    period_type = period_type.lower()
    labels = []
    values = []

    if period_type == 'day':
        # 24 hours in IST
        hourly_counts = {h: 0 for h in range(24)}
        for call_time in calls_qs.values_list('call_started_at', flat=True):
            h = call_time.astimezone(IST).hour
            hourly_counts[h] += 1

        for h in range(24):
            hour_dt = datetime(2026, 1, 1, h, 0)
            labels.append(hour_dt.strftime('%I %p'))  # e.g. 12 AM, 02 AM
            values.append(hourly_counts[h])

    elif period_type == 'week':
        # Mon-Sun
        start_date = start_dt.astimezone(IST).date()
        daily_counts = {}
        for i in range(7):
            d = start_date + timedelta(days=i)
            daily_counts[d] = 0

        for call_time in calls_qs.values_list('call_started_at', flat=True):
            d = call_time.astimezone(IST).date()
            if d in daily_counts:
                daily_counts[d] += 1

        for d, count in sorted(daily_counts.items()):
            labels.append(d.strftime('%a (%d %b)'))
            values.append(count)

    elif period_type == 'month':
        start_date = start_dt.astimezone(IST).date()
        end_date = end_dt.astimezone(IST).date()
        daily_counts = {}
        curr = start_date
        while curr <= end_date:
            daily_counts[curr] = 0
            curr += timedelta(days=1)

        for call_time in calls_qs.values_list('call_started_at', flat=True):
            d = call_time.astimezone(IST).date()
            if d in daily_counts:
                daily_counts[d] += 1

        for d, count in sorted(daily_counts.items()):
            labels.append(str(d.day))
            values.append(count)

    elif period_type == 'year':
        # 12 months
        year = start_dt.astimezone(IST).year
        monthly_counts = {m: 0 for m in range(1, 13)}
        for call_time in calls_qs.values_list('call_started_at', flat=True):
            dt_ist = call_time.astimezone(IST)
            if dt_ist.year == year:
                monthly_counts[dt_ist.month] += 1

        for m in range(1, 13):
            labels.append(datetime(2026, m, 1).strftime('%b'))
            values.append(monthly_counts[m])

    else:
        # Default fallback
        labels = ['Total Calls']
        values = [calls_qs.count()]

    return {
        'labels': labels,
        'values': values,
        'total': sum(values)
    }


def filter_call_report_leads(user, start_dt, end_dt, filters=None, sort_by='-updated_at'):
    """
    Evaluates the 11 filter conditions from Section 4.2:
    1. Call type (Incoming, Outgoing, Missed, Rejected, Not connected)
    2. Date (Exact date or range)
    3. Time of day (from HH to HH)
    4. By user (multi-select user IDs)
    5. User state (Working / On Leave / Invited)
    6. Duration (from X to Y, unit Sec/Min)
    7. Feedback is (Call outcome)
    8. Notes contain (text search)
    9. Recording is (Available / Not available)
    10. Lead status (multi-select statuses)
    11. Lead source (Facebook, WhatsApp, Google Calls, Walk-in, etc.)
    """
    filters = filters or {}

    # Start with call log query in period
    call_q = Q(call_started_at__gte=start_dt, call_started_at__lte=end_dt)

    # 1. Call Type
    call_types = filters.get('call_type')
    if call_types:
        if isinstance(call_types, str):
            call_types = [call_types]
        type_q = Q()
        for ct in call_types:
            ct_clean = ct.strip().lower()
            if ct_clean == 'incoming':
                type_q |= Q(call_status='Incoming')
            elif ct_clean == 'outgoing':
                type_q |= Q(call_status__in=['Completed', 'Connected', 'Dialing', 'Initiated'])
            elif ct_clean == 'missed':
                type_q |= Q(call_status='Missed')
            elif ct_clean == 'rejected':
                type_q |= Q(call_status__in=['Busy', 'Cancelled', 'Failed'])
            elif ct_clean in ['not connected', 'not_connected']:
                type_q |= Q(call_status__in=['No Answer', 'Missed', 'Failed', 'Cancelled'], duration=0)
            else:
                type_q |= Q(call_status__icontains=ct)
        call_q &= type_q

    # 3. Time of Day (Hour filter)
    time_from = filters.get('time_from')
    time_to = filters.get('time_to')
    if time_from is not None and str(time_from).isdigit():
        call_q &= Q(call_started_at__hour__gte=int(time_from))
    if time_to is not None and str(time_to).isdigit():
        call_q &= Q(call_started_at__hour__lte=int(time_to))

    # 4. By User
    by_users = filters.get('by_user')
    if by_users:
        if isinstance(by_users, str):
            by_users = [u.strip() for u in by_users.split(',') if u.strip()]
        call_q &= Q(caller_id__in=by_users)

    # 5. User State
    user_state = filters.get('user_state')
    if user_state:
        if user_state == 'Working':
            call_q &= Q(caller__is_active=True, caller__is_on_duty=True)
        elif user_state == 'On Leave':
            call_q &= Q(caller__is_active=True, caller__is_on_duty=False)
        elif user_state == 'Invited':
            call_q &= Q(caller__invitation_status='Invited')

    # 6. Duration range
    duration_from = filters.get('duration_from')
    duration_to = filters.get('duration_to')
    duration_unit = filters.get('duration_unit', 'sec').lower()
    mult = 60 if duration_unit == 'min' else 1

    if duration_from is not None and str(duration_from).replace('-', '').isdigit():
        call_q &= Q(duration__gte=int(duration_from) * mult)
    if duration_to is not None and str(duration_to).isdigit():
        call_q &= Q(duration__lte=int(duration_to) * mult)

    # 7. Feedback / Call outcome
    feedback = filters.get('feedback')
    if feedback:
        if isinstance(feedback, str):
            feedback = [feedback]
        call_q &= Q(call_outcome__in=feedback)

    # 8. Notes contain
    notes_contain = filters.get('notes_contain')
    if notes_contain:
        call_q &= Q(notes__icontains=notes_contain)

    # 9. Recording availability
    recording_is = filters.get('recording_is')
    if recording_is == 'Available':
        call_q &= ~Q(recording_url='') & Q(recording_url__isnull=False)
    elif recording_is == 'Not available':
        call_q &= Q(recording_url='') | Q(recording_url__isnull=True)

    calls_filtered = CallHistory.objects.filter(call_q)
    calls_filtered = scope_call_queryset_by_role(user, calls_filtered)
    matching_lead_ids = calls_filtered.values_list('lead_id', flat=True).distinct()

    # Query leads
    leads_qs = Lead.objects.filter(id__in=matching_lead_ids)
    leads_qs = scope_lead_queryset_by_role(user, leads_qs)

    # 10. Lead Status
    lead_status = filters.get('lead_status')
    if lead_status:
        if isinstance(lead_status, str):
            lead_status = [s.strip() for s in lead_status.split(',') if s.strip()]
        leads_qs = leads_qs.filter(status__in=lead_status)

    # 11. Lead Source
    lead_source = filters.get('lead_source')
    if lead_source:
        leads_qs = leads_qs.filter(Q(source__icontains=lead_source) | Q(channel__name__icontains=lead_source))

    # Sorting
    if sort_by in ['created_at', '-created_at', 'updated_at', '-updated_at', 'name', '-name']:
        leads_qs = leads_qs.order_by(sort_by)
    elif sort_by == 'newest_call':
        leads_qs = leads_qs.order_by('-calls__call_started_at').distinct()
    else:
        leads_qs = leads_qs.order_by('-updated_at')

    return leads_qs
