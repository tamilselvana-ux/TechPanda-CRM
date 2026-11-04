import re

# Item 38: admin/calls_list.html
p1 = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\admin\calls_list.html"
with open(p1, "r", encoding="utf-8") as f:
    c1 = f.read()
old1 = re.search(r'<div class="tp-smart-date-container[^"]*">\s*<input[^>]+name="date_from"[^>]*>\s*<input[^>]+name="date_to"[^>]*>\s*</div>', c1)
if old1:
    c1 = c1[:old1.start()] + '{% include "partials/date_range_picker.html" with from_name="date_from" to_name="date_to" from_val=date_from to_val=date_to %}' + c1[old1.end():]
    with open(p1, "w", encoding="utf-8") as f:
        f.write(c1)
    print("Updated admin/calls_list.html successfully")
else:
    print("Old block not found in admin/calls_list.html")

# Item 39: calls/recordings_list.html
p2 = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\calls\recordings_list.html"
with open(p2, "r", encoding="utf-8") as f:
    c2 = f.read()
old2 = re.search(r'<div class="tp-smart-date-container[^"]*">\s*<input[^>]+name="date_from"[^>]*>\s*<input[^>]+name="date_to"[^>]*>\s*</div>', c2)
if old2:
    c2 = c2[:old2.start()] + '{% include "partials/date_range_picker.html" with from_name="date_from" to_name="date_to" from_val=f.date_from to_val=f.date_to %}' + c2[old2.end():]
    with open(p2, "w", encoding="utf-8") as f:
        f.write(c2)
    print("Updated calls/recordings_list.html successfully")
else:
    print("Old block not found in calls/recordings_list.html")
