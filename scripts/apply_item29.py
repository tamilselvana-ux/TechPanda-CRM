import re

p = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\admin_dashboard\dashboard.html"
with open(p, "r", encoding="utf-8") as f:
    c = f.read()

# Replace tp-smart-date-container block
old_block = re.search(r'<div class="tp-smart-date-container compact w-100">.*?</div>\s*</div>', c, re.DOTALL)
if old_block:
    new_snippet = '{% include "partials/date_range_picker.html" with from_name="from_date" to_name="to_date" from_val=from_date to_val=to_date %}\n    </div>'
    c = c[:old_block.start()] + new_snippet + c[old_block.end():]
    with open(p, "w", encoding="utf-8") as f:
        f.write(c)
    print("Updated admin_dashboard/dashboard.html successfully")
else:
    print("Old block not found in admin_dashboard/dashboard.html")
