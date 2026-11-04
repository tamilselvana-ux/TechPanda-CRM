import os

p = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\base.html"
with open(p, "r", encoding="utf-8") as f:
    c = f.read()

target_css = """<link rel="stylesheet" href="{% static 'css/calendar-drawer.css' %}?v=20261030_v1">"""
new_css = target_css + """\n  <link rel="stylesheet" href="{% static 'css/date-range-picker.css' %}?v=20261030_compact">"""

target_js = """<script src="{% static 'js/calendar-drawer.js' %}?v=20261030_v1"></script>"""
new_js = target_js + """\n  <!-- Compact Date Range Picker -->\n  <script src="{% static 'js/date-range-picker.js' %}?v=20261030_compact"></script>"""

if target_css in c and target_js in c:
    c = c.replace(target_css, new_css, 1)
    c = c.replace(target_js, new_js, 1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(c)
    print("Updated base.html successfully")
else:
    print("Targets not found in base.html")
