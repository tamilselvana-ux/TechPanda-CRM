import os

path = 'templates/manager/leads_list.html' if os.path.exists('templates/manager/leads_list.html') else 'CRM/templates/manager/leads_list.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

target = '<a href="{% url \'manager_lead_detail\' ld.pk %}" class="btn btn-secondary btn-sm">View</a>'
replacement = '<button type="button" class="btn btn-primary btn-sm" data-open-360="{{ ld.pk }}" title="Quick 360° Timeline Drawer" style="font-weight: 700; padding: 2px 7px;">360°</button>\n              <a href="{% url \'manager_lead_detail\' ld.pk %}" class="btn btn-secondary btn-sm">View</a>'

if target in html and "data-open-360" not in html:
    html = html.replace(target, replacement, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("ADDED_360_BTN_TO_MANAGER_LEADS")
else:
    print("ALREADY_ADDED_OR_NOT_FOUND")
