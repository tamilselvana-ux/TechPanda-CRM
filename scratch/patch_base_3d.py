path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\base.html"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

target_css = '<link rel="stylesheet" href="{% static \'css/date-range-picker.css\' %}?v=20261030_compact">'
replace_css = '<link rel="stylesheet" href="{% static \'css/date-range-picker.css\' %}?v=20261030_compact">\n  <link rel="stylesheet" href="{% static \'css/modern-3d-cinematic.css\' %}?v=20261030_3d">'

target_js = '<script src="{% static \'js/date-range-picker.js\' %}?v=20261030_compact"></script>'
replace_js = '<script src="{% static \'js/date-range-picker.js\' %}?v=20261030_compact"></script>\n  <!-- 3D Cinematic Interactive Micro-Engine -->\n  <script src="{% static \'js/modern-3d-cinematic.js\' %}?v=20261030_3d" defer></script>'

norm = content.replace("\r\n", "\n")

if target_css in norm:
    norm = norm.replace(target_css, replace_css, 1)
    print("Added modern-3d-cinematic.css to base.html")
else:
    print("target_css not found")

if target_js in norm:
    norm = norm.replace(target_js, replace_js, 1)
    print("Added modern-3d-cinematic.js to base.html")
else:
    print("target_js not found")

with open(path, "w", encoding="utf-8") as f:
    f.write(norm)

print("base.html patched successfully!")
