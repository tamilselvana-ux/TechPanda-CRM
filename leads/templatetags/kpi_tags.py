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


@register.filter
def star_range(value):
    """Returns range(1, 6) for 5-star ratings."""
    return range(1, 6)


@register.filter
def user_initials(user):
    """Returns initials for avatar circle, e.g. 'AK'."""
    if not user:
        return 'U'
    fname = getattr(user, 'first_name', '') or ''
    lname = getattr(user, 'last_name', '') or ''
    if fname or lname:
        return f"{fname[:1]}{lname[:1]}".strip().upper() or 'U'
    username = getattr(user, 'username', '') or ''
    return username[:2].upper() if username else 'U'


@register.filter
def short_naturaltime(value):
    """Formats datetime as short natural time, e.g. '2h ago', '3d ago', 'just now'."""
    if not value:
        return ''
    from datetime import datetime
    from django.utils import timezone
    now = timezone.now()
    try:
        diff = now - value if (hasattr(value, 'tzinfo') and value.tzinfo) else datetime.now() - value
        seconds = int(diff.total_seconds())
    except Exception:
        return str(value)

    if seconds < 0:
        return 'just now'
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        return f"{seconds // 60}m ago"
    elif seconds < 86400:
        return f"{seconds // 3600}h ago"
    elif seconds < 604800:
        return f"{seconds // 86400}d ago"
    else:
        try:
            return value.strftime('%d %b')
        except Exception:
            return str(value)


