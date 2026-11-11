p = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\public\student_enquiry_form.html"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()

# Add html/body overflow guard
s = s.replace(
    "    body {\n",
    "    html, body {\n      max-width: 100%;\n      overflow-x: hidden;\n    }\n\n    body {\n"
)

# Fix invalid nested <label> inside Whatsapp form-label -> use <div class="form-label">
old_wa = '''          <label class="form-label" for="whatsapp_number">
            <span>Whatsapp</span>
            <label class="same-mobile-label">
              <input type="checkbox" id="sameAsMobileCb"> Same as Mobile
            </label>
          </label>'''

new_wa = '''          <div class="form-label">
            <label for="whatsapp_number" style="cursor:pointer;">Whatsapp</label>
            <label class="same-mobile-label">
              <input type="checkbox" id="sameAsMobileCb"> Same as Mobile
            </label>
          </div>'''

assert old_wa in s, "old_wa not found"
s = s.replace(old_wa, new_wa, 1)

with open(p, "w", encoding="utf-8") as f:
    f.write(s)
print("Cleaned mobile overflow guard and invalid nested label.")
