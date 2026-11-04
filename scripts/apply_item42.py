import re

p = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\reports\admin_reports.html"
with open(p, "r", encoding="utf-8") as f:
    c = f.read()

old_block = re.search(r'<div class="tp-smart-date-container[^"]*">\s*<input[^>]+name="date_from"[^>]*>\s*<input[^>]+name="date_to"[^>]*>\s*</div>', c)
if old_block:
    new_snippet = '{% include "partials/date_range_picker.html" with from_name="date_from" to_name="date_to" from_val=date_from to_val=date_to %}'
    c = c[:old_block.start()] + new_snippet + c[old_block.end():]
    with open(p, "w", encoding="utf-8") as f:
        f.write(c)
    print("Updated reports/admin_reports.html successfully")
else:
    print("Old block not found in reports/admin_reports.html")
