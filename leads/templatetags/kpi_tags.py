import urllib.parse
from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.simple_tag(takes_context=True)
def build_kpi_url(context, view_name, kpi_field=None, kpi_value=None, **kwargs):
    """
    Builds a drilldown URL preserving dashboard filters (branch, dates, manager, telecaller)
    while reconciling parameter mismatches (from_date/start_date -> date_from).
    Usage:
      {% build_kpi_url 'admin_leads_list' 'status' 'New' %}
      {% build_kpi_url 'admin_leads_list' 'view' 'all' %}
      {% build_kpi_url 'admin_leads_list' 'status_group' 'pipeline' %}
      {% build_kpi_url 'admin_followups_list' 'status' 'overdue' %}
      {% build_kpi_url 'admin_calls_list' 'status' 'Completed' %}
    """
    request = context.get('request')
    query_params = {}

    if request and hasattr(request, 'GET'):
        for k, v in request.GET.items():
            if v is not None and str(v).strip():
                query_params[k] = str(v).strip()

    # Reconcile date parameters across dashboard forms
    if 'from_date' in query_params:
        fd = query_params.pop('from_date')
        if 'date_from' not in query_params:
            query_params['date_from'] = fd
    if 'start_date' in query_params:
        sd = query_params.pop('start_date')
        if 'date_from' not in query_params:
            query_params['date_from'] = sd

    if 'to_date' in query_params:
        td = query_params.pop('to_date')
        if 'date_to' not in query_params:
            query_params['date_to'] = td
    if 'end_date' in query_params:
        ed = query_params.pop('end_date')
        if 'date_to' not in query_params:
            query_params['date_to'] = ed

    # Remove dashboard pagination parameter
    query_params.pop('page', None)

    # Inbound context branch from view if not in GET
    if 'branch' not in query_params:
        selected_branch_id = context.get('selected_branch_id')
        if selected_branch_id:
            query_params['branch'] = str(selected_branch_id)
        elif context.get('selected_branch'):
            sb = context.get('selected_branch')
            if hasattr(sb, 'id'):
                query_params['branch'] = str(sb.id)

    # If KPI sets a field/value
    if kpi_field and kpi_value is not None:
        query_params[kpi_field] = str(kpi_value)

    # Extra keyword arguments
    for k, v in kwargs.items():
        if v is not None and str(v).strip():
            query_params[k] = str(v).strip()

    # Total leads drilldown: when clicking total leads, we want to view ALL leads (not default all_active)
    if kpi_field == 'view' and kpi_value == 'all':
        query_params['view'] = 'all'
        query_params.pop('status', None)
        query_params.pop('status_group', None)

    # If status or status_group is set, ensure view doesn't conflict
    if 'status' in query_params or 'status_group' in query_params:
        if query_params.get('view') == 'all_active':
            query_params.pop('view', None)

    # Add friendly label if not provided
    if 'kpi_label' not in query_params and kpi_field and kpi_value:
        query_params['kpi_label'] = f"{kpi_field.replace('_', ' ').title()}: {kpi_value}"

    try:
        base_url = reverse(view_name)
    except NoReverseMatch:
        base_url = view_name if (view_name.startswith('/') or view_name.startswith('http')) else f"/{view_name}/"

    if query_params:
        encoded = urllib.parse.urlencode(query_params)
        return f"{base_url}?{encoded}"
    return base_url


from django.utils import timezone

@register.filter
def short_naturaltime(dt):
    """
    Returns short relative time like '4m ago', '23m ago', '1h ago', '2d ago'
    matching TeleCRM Image 2 format.
    """
    if not dt:
        return "-"
    now = timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    diff = now - dt
    total_seconds = int(diff.total_seconds())
    if total_seconds < 0:
        return "just now"
    if total_seconds < 60:
        return "just now"
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 7:
        return f"{days}d ago"
    weeks = days // 7
    if weeks < 4:
        return f"{weeks}w ago"
    return dt.strftime("%b %d, %Y")


@register.filter
def user_initials(user_or_name):
    """
    Extracts 2-letter uppercase initials for staff avatar badge, e.g. 'Shalini H' -> 'SH'
    """
    if not user_or_name:
        return "--"
    if hasattr(user_or_name, 'get_full_name'):
        name = user_or_name.get_full_name() or user_or_name.username
    else:
        name = str(user_or_name)
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    elif len(parts) == 1 and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    elif len(parts) == 1:
        return parts[0][:1].upper()
    return "--"


@register.filter
def star_range(val):
    """Generates a list [1, 2, 3, 4, 5] for rendering star icons."""
    return [1, 2, 3, 4, 5]

