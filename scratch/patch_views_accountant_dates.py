path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\views_accountant.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Update date calculation block in accountant_dashboard
old_date_calc = """    # 1. Date Range Filtering (Default to current month)
    from leads.utils_date_filter import extract_normalized_date_range
    today = timezone.localdate()
    _date_info = extract_normalized_date_range(request, default_period='month')
    start_date = _date_info['start_date_obj'] or today.replace(day=1)
    end_date = _date_info['end_date_obj'] or today
    start_date_str = _date_info['start_date'] or start_date.strftime('%Y-%m-%d')
    end_date_str = _date_info['end_date'] or end_date.strftime('%Y-%m-%d')
    start_dt = _date_info['start_dt'] or timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_dt = _date_info['end_dt'] or timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    # Edge Case: start_date > end_date (Gracefully report warning and default to current month without crashing)
    if start_date > end_date:
        messages.warning(request, "From Date cannot be later than To Date. Reset to current month.")
        start_date = today.replace(day=1)
        end_date = today
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_dt = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))"""

new_date_calc = """    # 1. Date Range Filtering (Default to current month)
    from leads.utils_date_filter import extract_normalized_date_range
    today = timezone.localdate()
    _date_info = extract_normalized_date_range(request, default_period='month')
    start_date = _date_info['start_date_obj'] or today.replace(day=1)
    end_date = _date_info['end_date_obj'] or today
    start_date_str = _date_info['start_date'] or start_date.strftime('%Y-%m-%d')
    end_date_str = _date_info['end_date'] or end_date.strftime('%Y-%m-%d')
    active_period = _date_info.get('period', 'month')

    # Edge Case: start_date > end_date (Gracefully report warning and default to current month without crashing)
    if start_date > end_date:
        messages.warning(request, "From Date cannot be after To Date. Reset to current month.")
        start_date = today.replace(day=1)
        end_date = today
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        active_period = 'month'

    start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_dt = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    showing_range_label = f"Showing: {start_date.strftime('%d %b %Y')} \u2013 {end_date.strftime('%d %b %Y')}" """

if old_date_calc in code:
    code = code.replace(old_date_calc, new_date_calc, 1)
    print("Replaced date calc block in views_accountant.py!")

# Update pending_queue_base to filter by selected date range
old_pending = """    # Pending Verification Queue (Oldest first)
    pending_queue_base = PaymentTransaction.objects.filter(
        enrollment__branch_id__in=branch_ids,
        status=PaymentTransactionStatus.PENDING_VERIFICATION
    )"""

new_pending = """    # Pending Verification Queue (Filtered by date range, oldest first)
    pending_queue_base = payment_base_qs.filter(
        status=PaymentTransactionStatus.PENDING_VERIFICATION
    )"""

if old_pending in code:
    code = code.replace(old_pending, new_pending, 1)
    print("Updated pending_queue_base to respect date range in views_accountant.py!")

# Update context with showing_range_label and active_period
old_ctx = """        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),"""

new_ctx = """        'start_date': start_date_str,
        'end_date': end_date_str,
        'from_date': start_date_str,
        'to_date': end_date_str,
        'active_period': active_period,
        'showing_range_label': showing_range_label,"""

if old_ctx in code:
    code = code.replace(old_ctx, new_ctx, 1)
    print("Updated context in views_accountant.py!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print("Finished patching views_accountant.py")
