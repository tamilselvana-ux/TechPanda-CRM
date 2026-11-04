dashboard_path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\admin_dashboard\dashboard.html"

with open(dashboard_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace <div class="tp-filter-field">\n      <label class="tp-field-label">Date Range</label>
old_date_field = '<div class="tp-filter-field">\n      <label class="tp-field-label">Date Range</label>'
new_date_field = '<div class="tp-filter-field tp-filter-field-date">\n      <label class="tp-field-label">Date Range</label>'

if old_date_field in content.replace("\r\n", "\n"):
    content_norm = content.replace("\r\n", "\n")
    content_norm = content_norm.replace(old_date_field, new_date_field, 1)
    
    old_action = """    <div class="tp-filter-action">
      <button type="submit" class="btn btn-primary tp-btn-primary btn-sm" style="font-size: 0.775rem; height: 33px; padding: 0 12px; display: inline-flex; align-items: center; gap: 4px;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
        Filter
      </button>
      <a href="{% url 'admin_dashboard' %}" class="btn btn-secondary tp-btn-secondary btn-sm" style="font-size: 0.775rem; height: 33px; padding: 0 10px; display: inline-flex; align-items: center;" title="Reset Filters">
        Reset
      </a>
    </div>"""

    new_action = """    <div class="tp-filter-action" style="display: flex; gap: 8px; align-items: flex-end;">
      <button type="submit" class="btn btn-primary tp-btn-primary btn-sm" style="font-size: 0.775rem; font-weight: 600; height: 34px; padding: 0 14px; display: inline-flex; align-items: center; gap: 5px;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
        Filter
      </button>
      <a href="{% url 'admin_dashboard' %}" class="btn btn-secondary tp-btn-secondary btn-sm" style="font-size: 0.775rem; font-weight: 600; height: 34px; padding: 0 12px; display: inline-flex; align-items: center;" title="Reset Filters">
        Reset
      </a>
    </div>"""

    if old_action in content_norm:
        content_norm = content_norm.replace(old_action, new_action, 1)
        print("Replaced action buttons in dashboard.html")
    else:
        print("Old action not found in dashboard.html")

    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(content_norm)
    print("dashboard.html updated successfully!")
else:
    print("Old date field not found in dashboard.html")
