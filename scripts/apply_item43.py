import re

p = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\reports\dashboard_report.html"
with open(p, "r", encoding="utf-8") as f:
    c = f.read()

# Replace reportSmartDateContainer with compact date picker wrapped in form
old_container = re.search(
    r'<!-- Custom Date Smart Calendar Anchored Silently -->\s*<div class="tp-smart-date-container"[^>]*>.*?</div>',
    c,
    re.DOTALL
)

if old_container:
    new_snippet = '''<!-- Compact Date Range Picker -->
      <form method="GET" action="" id="dashboardReportDateForm" style="display: inline-flex; align-items: center; margin: 0;">
        {% if branch_filter %}<input type="hidden" name="branch" value="{{ branch_filter }}">{% endif %}
        {% if channel_filter %}<input type="hidden" name="channel" value="{{ channel_filter }}">{% endif %}
        {% include "partials/date_range_picker.html" with from_name="start_date" to_name="end_date" from_val=start_date to_val=end_date period_name="date_filter" period_val="custom" %}
      </form>'''
    c = c[:old_container.start()] + new_snippet + c[old_container.end():]

# Remove old #customDateModal
c = re.sub(
    r'<!-- Custom Date Range Modal -->\s*<div id="customDateModal".*?</div>\s*</div>\s*</div>',
    '',
    c,
    flags=re.DOTALL
)

with open(p, "w", encoding="utf-8") as f:
    f.write(c)

print("Updated reports/dashboard_report.html successfully")
