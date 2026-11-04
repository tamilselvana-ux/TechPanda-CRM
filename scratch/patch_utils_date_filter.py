path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\utils_date_filter.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update parameter extraction to support 'from' and 'to'
old_params = "raw_start = (get.get('start_date') or get.get('from_date') or get.get('date_from') or '').strip()\n    raw_end = (get.get('end_date') or get.get('to_date') or get.get('date_to') or '').strip()"
new_params = "raw_start = (get.get('from') or get.get('start_date') or get.get('from_date') or get.get('date_from') or '').strip()\n    raw_end = (get.get('to') or get.get('end_date') or get.get('to_date') or get.get('date_to') or '').strip()"

if old_params in code:
    code = code.replace(old_params, new_params, 1)
    print("Updated raw_start/raw_end extraction to support 'from' and 'to' aliases!")

# 2. Add 'this_fy' / 'financial_year' preset
old_presets = """    elif period == 'last_month':
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        start_date_obj = last_day_last_month.replace(day=1)
        end_date_obj = last_day_last_month"""

new_presets = """    elif period == 'last_month':
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        start_date_obj = last_day_last_month.replace(day=1)
        end_date_obj = last_day_last_month
    elif period in ('this_fy', 'fy', 'financial_year'):
        if today.month >= 4:
            start_date_obj = date(today.year, 4, 1)
        else:
            start_date_obj = date(today.year - 1, 4, 1)
        end_date_obj = today"""

if old_presets in code:
    code = code.replace(old_presets, new_presets, 1)
    print("Added this_fy preset to utils_date_filter.py!")

# 3. Add 'from' and 'to' to returned dictionary
old_dict = "        'start_date': start_date_str,\n        'end_date': end_date_str,"
new_dict = "        'from': start_date_str,\n        'to': end_date_str,\n        'start_date': start_date_str,\n        'end_date': end_date_str,"

if old_dict in code:
    code = code.replace(old_dict, new_dict, 1)
    print("Added from and to aliases to returned dictionary!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated utils_date_filter.py successfully!")
