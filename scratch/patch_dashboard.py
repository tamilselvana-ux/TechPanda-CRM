import os

path = 'templates/receptionist/dashboard.html' if os.path.exists('templates/receptionist/dashboard.html') else 'CRM/templates/receptionist/dashboard.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update counselor selects with On Duty / Out of Office status
old_opt1 = '<option value="{{ c.id }}">{{ c.get_full_name|default:c.username }} (Counselor)</option>'
new_opt1 = '<option value="{{ c.id }}">{% if c.is_on_duty %}🟢 [On Duty]{% else %}🔴 [Out of Office]{% endif %} {{ c.get_full_name|default:c.username }} (Counselor)</option>'

if old_opt1 in html:
    html = html.replace(old_opt1, new_opt1)
    print("Replaced counselor options")
else:
    print("old_opt1 not found")

# 2. Add IDs to course and category selects in registerStudentModal
old_course_select = '<select name="product_id" class="form-select">'
new_course_select = '<select name="product_id" id="regCourseSelect" class="form-select">'
if old_course_select in html:
    html = html.replace(old_course_select, new_course_select, 1)
    print("Replaced course select ID")

old_cat_select = '<select name="category" class="form-select">'
new_cat_select = '<select name="category" id="regCategorySelect" class="form-select">'
if old_cat_select in html:
    html = html.replace(old_cat_select, new_cat_select, 1)
    print("Replaced category select ID")

old_counselor_select = '<select name="counselor_id" class="form-select" {% if not has_counselors %}disabled{% endif %}>'
new_counselor_select = '<select name="counselor_id" id="regCounselorSelect" class="form-select" {% if not has_counselors %}disabled{% endif %}>'
if old_counselor_select in html:
    html = html.replace(old_counselor_select, new_counselor_select, 1)
    print("Replaced counselor select ID")

# 3. Add Counselor Live Duty Status bar right after KPI grid
duty_bar = """
<!-- COUNSELOR LIVE DUTY STATUS BAR -->
{% if counselors %}
<div class="tp-card" style="padding: 12px 18px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
  <div style="display: flex; align-items: center; gap: 8px;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
    <span style="font-size: 0.88rem; font-weight: 700; color: #1e293b;">Branch Counselors Live Status:</span>
  </div>
  <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
    {% for c in counselors %}
      <span class="badge" style="font-size: 0.8rem; font-weight: 600; padding: 5px 12px; border-radius: 9999px; display: inline-flex; align-items: center; gap: 6px; {% if c.is_on_duty %}background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0;{% else %}background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca;{% endif %}">
        {% if c.is_on_duty %}
          <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #10b981;"></span>
          <strong>{{ c.get_full_name|default:c.username }}</strong> &bull; Free / On Duty
        {% else %}
          <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #ef4444;"></span>
          <strong>{{ c.get_full_name|default:c.username }}</strong> &bull; Out of Office
        {% endif %}
      </span>
    {% endfor %}
  </div>
</div>
{% endif %}
"""

kpi_end = "<!-- FILTERS CARD -->"
if kpi_end in html:
    html = html.replace(kpi_end, duty_bar + "\n" + kpi_end, 1)
    print("Inserted duty status bar")

# 4. Enhance handlePhoneInput and add instant autoFillWalkin function
old_handle_phone = """let phoneCheckTimeout;
function handlePhoneInput(phone) {"""

new_handle_phone = """let phoneCheckTimeout;
let latestPreCheckMatches = [];

function autoFillWalkin(matchId) {
  const m = latestPreCheckMatches.find(x => x.id === matchId) || latestPreCheckMatches[0];
  if (!m) return;
  if (m.name) document.getElementById('regStudentName').value = m.name;
  if (m.email) document.getElementById('regStudentEmail').value = m.email;
  if (m.course_id) {
    const courseSelect = document.getElementById('regCourseSelect');
    if (courseSelect) courseSelect.value = m.course_id;
  }
  if (m.category) {
    const catSelect = document.getElementById('regCategorySelect');
    if (catSelect) catSelect.value = m.category;
  }
  if (m.assigned_counselor_id) {
    const counSelect = document.getElementById('regCounselorSelect');
    if (counSelect && counSelect.querySelector(`option[value="${m.assigned_counselor_id}"]`)) {
      counSelect.value = m.assigned_counselor_id;
    }
  }
  const autoBanner = document.getElementById('autoFillSuccessBanner');
  if (autoBanner) {
    autoBanner.style.display = 'block';
    autoBanner.innerHTML = `⚡ <strong>1-Sec Pre-Fill Applied:</strong> Restored details for <em>${m.name}</em> (Course: ${m.course_name || 'N/A'}).`;
    setTimeout(() => { autoBanner.style.display = 'none'; }, 5000);
  }
}

function handlePhoneInput(phone) {"""

if old_handle_phone in html:
    html = html.replace(old_handle_phone, new_handle_phone, 1)
    print("Added autoFillWalkin helper")

# In handlePhoneInput result handling, store matches and add instant 1-sec button & auto-fill on 10 digits
target_fetch_block = """      if (data.success && data.has_matches) {
        warnBox.style.display = 'block';"""

replacement_fetch_block = """      if (data.success && data.has_matches) {
        latestPreCheckMatches = data.matches;
        warnBox.style.display = 'block';
        
        // Instant pre-fill if single clear match and name is currently blank
        const nameField = document.getElementById('regStudentName');
        if (data.matches.length === 1 && (!nameField.value || nameField.value.trim() === '')) {
          autoFillWalkin(data.matches[0].id);
        }"""

if target_fetch_block in html:
    html = html.replace(target_fetch_block, replacement_fetch_block, 1)
    print("Added automatic prefill execution")

# Add 1-sec Pre-fill button inside duplicate matches HTML
old_match_buttons = """            <div style="margin-top: 6px; display: flex; gap: 6px;">
              <button type="button" class="btn btn-secondary" style="font-size: 0.725rem; padding: 2px 8px;" onclick="closeRegisterStudentModal(); openLeadHistoryModal(${m.id});">
                View History
              </button>"""

new_match_buttons = """            <div style="margin-top: 6px; display: flex; gap: 6px; flex-wrap: wrap;">
              <button type="button" class="btn btn-success" style="font-size: 0.725rem; padding: 2px 8px; background: #059669; color: #fff; font-weight: 700; border: none; border-radius: 4px;" onclick="autoFillWalkin(${m.id})">
                ⚡ 1-Sec Instant Pre-fill
              </button>
              <button type="button" class="btn btn-secondary" style="font-size: 0.725rem; padding: 2px 8px;" onclick="closeRegisterStudentModal(); openLeadHistoryModal(${m.id});">
                View History
              </button>"""

if old_match_buttons in html:
    html = html.replace(old_match_buttons, new_match_buttons, 1)
    print("Added 1-Sec Instant Pre-fill button to card")

# Add autoFillSuccessBanner right above duplicateWarningBox
old_warn_box = '<div id="duplicateWarningBox"'
new_warn_box = """<div id="autoFillSuccessBanner" style="display: none; background: #ecfdf5; border: 1px solid #a7f3d0; border-left: 4px solid #10b981; border-radius: 6px; padding: 10px 14px; margin-bottom: 14px; font-size: 0.85rem; color: #065f46;"></div>
      <div id="duplicateWarningBox" """

if old_warn_box in html:
    html = html.replace(old_warn_box, new_warn_box, 1)
    print("Added autoFillSuccessBanner container")

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("ALL_DASHBOARD_PATCHES_APPLIED")
