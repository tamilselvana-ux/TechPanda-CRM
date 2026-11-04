import os
import re

base_dir = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM"
templates_dir = os.path.join(base_dir, "templates")

templates = [
    ("admin_dashboard/dashboard.html", "from_date", "to_date", None, None),
    ("accountant/dashboard.html", "start_date", "end_date", None, None),
    ("accountant/verification_list.html", "start_date", "end_date", None, None),
    ("admin/leads_list.html", "date_from", "date_to", None, None),
    ("admin/new_leads_list.html", "date_from", "date_to", None, None),
    ("branch_head_dashboard/dashboard.html", "start_date", "end_date", "period", "custom"),
    ("counselor_dashboard/dashboard.html", "start_date", "end_date", "period", "custom"),
    ("manager_dashboard/dashboard.html", "start_date", "end_date", "period", "custom"),
    ("telecaller_dashboard/dashboard.html", "start_date", "end_date", "period", "custom"),
    ("admin/calls_list.html", "date_from", "date_to", None, None),
    ("calls/recordings_list.html", "date_from", "date_to", None, None),
    ("admin/followups_list.html", "date_from", "date_to", None, None),
    ("counselor/followups_list.html", "date_from", "date_to", None, None),
    ("reports/admin_reports.html", "date_from", "date_to", None, None),
    ("reports/dashboard_report.html", "start_date", "end_date", "date_filter", "custom"),
    ("reports/telecaller_rnr_report.html", "start_date", "end_date", "period", "custom"),
    ("finance/dashboard.html", "start_date", "end_date", "period", "custom"),
    ("receptionist/dashboard.html", "from_date", "to_date", None, None),
]

for tmpl, from_name, to_name, period_name, period_val in templates:
    p = os.path.join(templates_dir, tmpl)
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Locate where inputs or calendar drawer triggers are
    lines = text.splitlines()
    print("=" * 60)
    print(tmpl)
    found = False
    for i, l in enumerate(lines):
        if any(k in l for k in ["calendar-drawer-trigger", "tp-smart-date-container", "customStartDate", "id=\"startDate\""]):
            start_i = max(0, i - 3)
            end_i = min(len(lines), i + 10)
            print(f"Lines {start_i+1}-{end_i}:")
            for j in range(start_i, end_i):
                print(f"  {j+1}: {lines[j]}")
            found = True
            break
    if not found:
        print("  NO trigger/container pattern found directly. Searching date input names...")
        for i, l in enumerate(lines):
            if from_name in l and ("input" in l or "type=" in l):
                start_i = max(0, i - 2)
                end_i = min(len(lines), i + 8)
                print(f"Lines {start_i+1}-{end_i}:")
                for j in range(start_i, end_i):
                    print(f"  {j+1}: {lines[j]}")
                break
