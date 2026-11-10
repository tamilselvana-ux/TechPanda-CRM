path = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\fb_leads\templates\fb_leads\leads.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update total KPI link
old_kpi1 = '''  <a href="?{% if selected_form %}form={{ selected_form|urlencode }}&{% endif %}{% if selected_ad %}ad={{ selected_ad|urlencode }}&{% endif %}{% if q %}q={{ q|urlencode }}{% endif %}" class="kpi-card"'''
new_kpi1 = '''  <a href="?{% if selected_form %}form={{ selected_form|urlencode }}&{% endif %}{% if selected_ad %}ad={{ selected_ad|urlencode }}&{% endif %}{% if date_from %}&date_from={{ date_from }}&{% endif %}{% if date_to %}&date_to={{ date_to }}&{% endif %}{% if q %}q={{ q|urlencode }}{% endif %}" class="kpi-card"'''
assert old_kpi1 in content, "old_kpi1 not found"
content = content.replace(old_kpi1, new_kpi1, 1)

# 2. Update error KPI link
old_kpi2 = '''  <a href="?crm=error{% if selected_form %}&form={{ selected_form|urlencode }}{% endif %}{% if selected_ad %}&ad={{ selected_ad|urlencode }}{% endif %}{% if q %}&q={{ q|urlencode }}{% endif %}" class="kpi-card"'''
new_kpi2 = '''  <a href="?crm=error{% if selected_form %}&form={{ selected_form|urlencode }}{% endif %}{% if selected_ad %}&ad={{ selected_ad|urlencode }}{% endif %}{% if date_from %}&date_from={{ date_from }}{% endif %}{% if date_to %}&date_to={{ date_to }}{% endif %}{% if q %}&q={{ q|urlencode }}{% endif %}" class="kpi-card"'''
assert old_kpi2 in content, "old_kpi2 not found"
content = content.replace(old_kpi2, new_kpi2, 1)

# 3. Add date fields into filter form
old_form = '''    <div class="filter-col" style="flex: 2; min-width: 200px;">
      <label style="font-size: 0.8rem; font-weight: 700; color: var(--tp-text-muted); text-transform: uppercase; margin-bottom: 4px; display: block;">Ad Creative</label>
      <select name="ad" class="form-select" onchange="this.form.submit()" style="border-radius: 8px;">
        <option value="">All Ad Creatives ({{ available_ads|length }})</option>
        {% for a in available_ads %}
        <option value="{{ a }}" {% if selected_ad == a %}selected{% endif %}>{{ a }}</option>
        {% endfor %}
      </select>
    </div>

    {% if crm_filter == 'error' %}'''

new_form = '''    <div class="filter-col" style="flex: 2; min-width: 200px;">
      <label style="font-size: 0.8rem; font-weight: 700; color: var(--tp-text-muted); text-transform: uppercase; margin-bottom: 4px; display: block;">Ad Creative</label>
      <select name="ad" class="form-select" onchange="this.form.submit()" style="border-radius: 8px;">
        <option value="">All Ad Creatives ({{ available_ads|length }})</option>
        {% for a in available_ads %}
        <option value="{{ a }}" {% if selected_ad == a %}selected{% endif %}>{{ a }}</option>
        {% endfor %}
      </select>
    </div>

    <div class="filter-col" style="flex: 1.5; min-width: 140px;">
      <label style="font-size: 0.8rem; font-weight: 700; color: var(--tp-text-muted); text-transform: uppercase; margin-bottom: 4px; display: block;">From Date</label>
      <input type="date" name="date_from" id="filterDateFrom" value="{{ date_from }}" class="form-control" style="border-radius: 8px;">
    </div>

    <div class="filter-col" style="flex: 1.5; min-width: 140px;">
      <label style="font-size: 0.8rem; font-weight: 700; color: var(--tp-text-muted); text-transform: uppercase; margin-bottom: 4px; display: block;">To Date</label>
      <input type="date" name="date_to" id="filterDateTo" value="{{ date_to }}" class="form-control" style="border-radius: 8px;">
    </div>

    {% if crm_filter == 'error' %}'''

assert old_form in content, "old_form not found"
content = content.replace(old_form, new_form, 1)

# 4. Add Quick Date Presets and active filter pills
old_pills = '''  {% if selected_form or selected_ad or crm_filter == 'error' %}
  <!-- Active Filter Pills -->
  <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--tp-surface-border, #e2e8f0); display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
    <span style="font-size: 0.78rem; font-weight: 700; color: var(--tp-text-muted);">Active Filters:</span>'''

new_pills = '''  <div style="display: flex; gap: 6px; align-items: center; margin-top: 10px; flex-wrap: wrap;">
    <span style="font-size: 0.76rem; font-weight: 700; color: var(--tp-text-muted); margin-right: 4px;">Quick Dates:</span>
    <button type="button" class="btn btn-sm" onclick="setLeadDatePreset('today')" style="background: #f1f5f9; color: #334155; font-size: 0.76rem; padding: 3px 8px; border-radius: 6px; border: 1px solid #cbd5e1;">Today</button>
    <button type="button" class="btn btn-sm" onclick="setLeadDatePreset('yesterday')" style="background: #f1f5f9; color: #334155; font-size: 0.76rem; padding: 3px 8px; border-radius: 6px; border: 1px solid #cbd5e1;">Yesterday</button>
    <button type="button" class="btn btn-sm" onclick="setLeadDatePreset('7days')" style="background: #f1f5f9; color: #334155; font-size: 0.76rem; padding: 3px 8px; border-radius: 6px; border: 1px solid #cbd5e1;">Last 7 Days</button>
    <button type="button" class="btn btn-sm" onclick="setLeadDatePreset('this_month')" style="background: #f1f5f9; color: #334155; font-size: 0.76rem; padding: 3px 8px; border-radius: 6px; border: 1px solid #cbd5e1;">This Month</button>
    <button type="button" class="btn btn-sm" onclick="setLeadDatePreset('clear')" style="background: #f8fafc; color: #64748b; font-size: 0.76rem; padding: 3px 8px; border-radius: 6px; border: 1px dashed #cbd5e1;">Clear Dates</button>
  </div>

  {% if selected_form or selected_ad or date_from or date_to or crm_filter == 'error' %}
  <!-- Active Filter Pills -->
  <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--tp-surface-border, #e2e8f0); display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
    <span style="font-size: 0.78rem; font-weight: 700; color: var(--tp-text-muted);">Active Filters:</span>
    {% if date_from or date_to %}
    <span class="badge" style="background: #ecfdf5; color: #047857; padding: 5px 10px; border-radius: 6px; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 6px;">
      Date: {{ date_from|default:"Beginning" }} to {{ date_to|default:"Today" }}
      <a href="?{% if selected_form %}form={{ selected_form|urlencode }}&{% endif %}{% if selected_ad %}ad={{ selected_ad|urlencode }}&{% endif %}{% if q %}q={{ q|urlencode }}&{% endif %}{% if crm_filter %}crm={{ crm_filter }}{% endif %}" style="color: #047857; text-decoration: none; font-weight: 800;">&times;</a>
    </span>
    {% endif %}'''

assert old_pills in content, "old_pills not found"
content = content.replace(old_pills, new_pills, 1)

# 5. Update pagination links
old_prev = '''href="?page={{ page.previous_page_number }}{% if q %}&q={{ q|urlencode }}{% endif %}{% if selected_form %}&form={{ selected_form|urlencode }}{% endif %}{% if selected_ad %}&ad={{ selected_ad|urlencode }}{% endif %}{% if crm_filter %}&crm={{ crm_filter }}{% endif %}">'''
new_prev = '''href="?page={{ page.previous_page_number }}{% if q %}&q={{ q|urlencode }}{% endif %}{% if selected_form %}&form={{ selected_form|urlencode }}{% endif %}{% if selected_ad %}&ad={{ selected_ad|urlencode }}{% endif %}{% if date_from %}&date_from={{ date_from }}{% endif %}{% if date_to %}&date_to={{ date_to }}{% endif %}{% if crm_filter %}&crm={{ crm_filter }}{% endif %}">'''
assert old_prev in content, "old_prev not found"
content = content.replace(old_prev, new_prev, 1)

old_next = '''href="?page={{ page.next_page_number }}{% if q %}&q={{ q|urlencode }}{% endif %}{% if selected_form %}&form={{ selected_form|urlencode }}{% endif %}{% if selected_ad %}&ad={{ selected_ad|urlencode }}{% endif %}{% if crm_filter %}&crm={{ crm_filter }}{% endif %}">'''
new_next = '''href="?page={{ page.next_page_number }}{% if q %}&q={{ q|urlencode }}{% endif %}{% if selected_form %}&form={{ selected_form|urlencode }}{% endif %}{% if selected_ad %}&ad={{ selected_ad|urlencode }}{% endif %}{% if date_from %}&date_from={{ date_from }}{% endif %}{% if date_to %}&date_to={{ date_to }}{% endif %}{% if crm_filter %}&crm={{ crm_filter }}{% endif %}">'''
assert old_next in content, "old_next not found"
content = content.replace(old_next, new_next, 1)

# 6. Update pollUrl in script
old_poll = '''const pollUrl = "{% url 'fb_leads:facebook_leads_recent_api' %}?q={{ q|urlencode }}{% if selected_form %}&form={{ selected_form|urlencode }}{% endif %}{% if selected_ad %}&ad={{ selected_ad|urlencode }}{% endif %}{% if crm_filter %}&crm={{ crm_filter }}{% endif %}";'''
new_poll = '''const pollUrl = "{% url 'fb_leads:facebook_leads_recent_api' %}?q={{ q|urlencode }}{% if selected_form %}&form={{ selected_form|urlencode }}{% endif %}{% if selected_ad %}&ad={{ selected_ad|urlencode }}{% endif %}{% if date_from %}&date_from={{ date_from }}{% endif %}{% if date_to %}&date_to={{ date_to }}{% endif %}{% if crm_filter %}&crm={{ crm_filter }}{% endif %}";'''
assert old_poll in content, "old_poll not found"
content = content.replace(old_poll, new_poll, 1)

# 7. Add setLeadDatePreset JS function
js_func = '''
function setLeadDatePreset(preset) {
  const dFrom = document.getElementById('filterDateFrom');
  const dTo = document.getElementById('filterDateTo');
  if (!dFrom || !dTo) return;
  const now = new Date();
  const format = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  };

  if (preset === 'today') {
    const todayStr = format(now);
    dFrom.value = todayStr;
    dTo.value = todayStr;
  } else if (preset === 'yesterday') {
    const yest = new Date(now);
    yest.setDate(yest.getDate() - 1);
    const yestStr = format(yest);
    dFrom.value = yestStr;
    dTo.value = yestStr;
  } else if (preset === '7days') {
    const past = new Date(now);
    past.setDate(past.getDate() - 7);
    dFrom.value = format(past);
    dTo.value = format(now);
  } else if (preset === 'this_month') {
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    dFrom.value = format(firstDay);
    dTo.value = format(now);
  } else if (preset === 'clear') {
    dFrom.value = '';
    dTo.value = '';
  }
  dFrom.form.submit();
}
'''

content += js_func

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched fb_leads/templates/fb_leads/leads.html")
