import re

p = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\finance\dashboard.html"
with open(p, "r", encoding="utf-8") as f:
    c = f.read()

old_block = re.search(r'<div class="tp-smart-date-container compact">\s*<input[^>]+name="start_date"[^>]*>\s*<input[^>]+name="end_date"[^>]*>\s*</div>', c)
if old_block:
    new_snippet = '{% include "partials/date_range_picker.html" with from_name="start_date" to_name="end_date" from_val=start_date to_val=end_date period_name="period" period_val="custom" %}'
    c = c[:old_block.start()] + new_snippet + c[old_block.end():]
    with open(p, "w", encoding="utf-8") as f:
        f.write(c)
    print("Updated finance/dashboard.html successfully")
else:
    print("Old block not found in finance/dashboard.html")
