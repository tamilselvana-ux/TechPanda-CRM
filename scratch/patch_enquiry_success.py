p = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\public\student_enquiry_success.html"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()

old = '        {% if branch %}\n        <span>📍 {{ branch.name }} Branch</span>\n        {% endif %}\n        <span>🕒 {{ submitted_at|date:"h:i A" }}</span>'
new = '        {% if branch %}\n        <span>📍 {{ branch.name }} Branch</span>\n        {% endif %}\n        {% if lead.custom_fields.enquiry_form_no %}\n        <span>📄 Form: {{ lead.custom_fields.enquiry_form_no }}</span>\n        {% endif %}\n        <span>🕒 {{ submitted_at|date:"h:i A" }}</span>'
assert old in s, "target not found"
s = s.replace(old, new, 1)
with open(p, "w", encoding="utf-8") as f:
    f.write(s)
print("Successfully patched student_enquiry_success.html")
