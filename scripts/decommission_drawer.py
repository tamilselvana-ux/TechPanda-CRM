import re

p = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\base.html"
with open(p, "r", encoding="utf-8") as f:
    c = f.read()

# Remove calendar-drawer.css
c = re.sub(r'\s*<link rel="stylesheet" href="{% static \'css/calendar-drawer\.css\' %}[^"]*">', '', c)

# Remove calendar_drawer.html include and calendar-drawer.js script
c = re.sub(r'\s*<!-- Global Shared Calendar Drawer -->', '', c)
c = re.sub(r'\s*{% include [\'"]components/calendar_drawer\.html[\'"] %}', '', c)
c = re.sub(r'\s*<script src="{% static \'js/calendar-drawer\.js\' %}[^"]*"></script>', '', c)

with open(p, "w", encoding="utf-8") as f:
    f.write(c)

print("Decommissioned obsolete calendar drawer from base.html successfully")
