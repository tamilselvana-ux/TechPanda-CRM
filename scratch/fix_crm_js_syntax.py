p_js = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\static\js\crm.js"
with open(p_js, "r", encoding="utf-8") as f:
    s = f.read()

old1 = '          waBtn.role="button" tabindex="0";'
new1 = '          waBtn.removeAttribute("href");\n          waBtn.setAttribute("role", "button");\n          waBtn.setAttribute("tabindex", "0");'
assert old1 in s, "old1 not found"
s = s.replace(old1, new1, 1)

old2 = '          emailBtn.role="button" tabindex="0";'
new2 = '          emailBtn.removeAttribute("href");\n          emailBtn.setAttribute("role", "button");\n          emailBtn.setAttribute("tabindex", "0");'
assert old2 in s, "old2 not found"
s = s.replace(old2, new2, 1)

with open(p_js, "w", encoding="utf-8") as f:
    f.write(s)

p_base = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\base.html"
with open(p_base, "r", encoding="utf-8") as fb:
    sb = fb.read()

old_v = "crm.js' %}?v=20261024_pwd_ui_cure"
new_v = "crm.js' %}?v=20261111_sidebar_fix"
assert old_v in sb, "old_v not found in base.html"
sb = sb.replace(old_v, new_v, 1)

with open(p_base, "w", encoding="utf-8") as fb:
    fb.write(sb)

print("Successfully fixed crm.js lines 1099 & 1112 and updated base.html cache buster.")
