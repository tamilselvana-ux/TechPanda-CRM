import re

p = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\receptionist\dashboard.html"
with open(p, "r", encoding="utf-8") as f:
    c = f.read()

old_block = re.search(r'<div class="tp-smart-date-container[^"]*">\s*<input[^>]+name="from_date"[^>]*>\s*<input[^>]+name="to_date"[^>]*>\s*</div>', c)
if old_block:
    new_snippet = '{% include "partials/date_range_picker.html" with from_name="from_date" to_name="to_date" from_val=from_date to_val=to_date %}'
    c = c[:old_block.start()] + new_snippet + c[old_block.end():]
    with open(p, "w", encoding="utf-8") as f:
        f.write(c)
    print("Updated receptionist/dashboard.html successfully")
else:
    print("Old block not found in receptionist/dashboard.html")
