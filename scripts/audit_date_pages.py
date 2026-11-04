import os
import re
import sys

base_dir = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM"
templates_dir = os.path.join(base_dir, "templates")

pages = [
    {
        "id": 1,
        "name": "Admin Dashboard",
        "url": "/admin/dashboard/",
        "template": "admin_dashboard/dashboard.html",
        "view": "leads.views.admin_dashboard",
    },
    {
        "id": 2,
        "name": "Accountant Dashboard",
        "url": "/accountant/dashboard/",
        "template": "accountant/dashboard.html",
        "view": "accounts.views.accountant_dashboard",
    },
    {
        "id": 3,
        "name": "Accountant Payment Verification",
        "url": "/accountant/verification/",
        "template": "accountant/verification_list.html",
        "view": "accounts.views.verification_list",
    },
    {
        "id": 4,
        "name": "Admin Leads List",
        "url": "/admin/leads/",
        "template": "admin/leads_list.html",
        "view": "leads.views.leads_list",
    },
    {
        "id": 5,
        "name": "Admin New Leads List",
        "url": "/admin/leads/new/",
        "template": "admin/new_leads_list.html",
        "view": "leads.views.new_leads_list",
    },
    {
        "id": 6,
        "name": "Branch Head Dashboard",
        "url": "/manager/branch-head/dashboard/",
        "template": "branch_head_dashboard/dashboard.html",
        "view": "leads.views.branch_head_dashboard",
    },
    {
        "id": 7,
        "name": "Counselor Dashboard",
        "url": "/counselor/dashboard/",
        "template": "counselor_dashboard/dashboard.html",
        "view": "leads.views.counselor_dashboard",
    },
    {
        "id": 8,
        "name": "Manager Dashboard",
        "url": "/manager/dashboard/",
        "template": "manager_dashboard/dashboard.html",
        "view": "leads.views.manager_dashboard",
    },
    {
        "id": 9,
        "name": "Telecaller Dashboard",
        "url": "/telecaller/dashboard/",
        "template": "telecaller_dashboard/dashboard.html",
        "view": "leads.views.telecaller_dashboard",
    },
    {
        "id": 10,
        "name": "Admin Calls List",
        "url": "/admin/calls/",
        "template": "admin/calls_list.html",
        "view": "calls.views.calls_list",
    },
    {
        "id": 11,
        "name": "Call Recordings List",
        "url": "/call-recordings/recordings/",
        "template": "calls/recordings_list.html",
        "view": "calls.views.recordings_list",
    },
    {
        "id": 12,
        "name": "Admin Followups List",
        "url": "/admin/followups/",
        "template": "admin/followups_list.html",
        "view": "leads.views.admin_followups_list",
    },
    {
        "id": 13,
        "name": "Counselor Followups List",
        "url": "/counselor/followups/",
        "template": "counselor/followups_list.html",
        "view": "leads.views.counselor_followups_list",
    },
    {
        "id": 14,
        "name": "Admin Reports",
        "url": "/admin/reports/",
        "template": "reports/admin_reports.html",
        "view": "leads.views.admin_reports",
    },
    {
        "id": 15,
        "name": "Manager Reports",
        "url": "/manager/reports/",
        "template": "reports/dashboard_report.html",
        "view": "leads.views.manager_reports",
    },
    {
        "id": 16,
        "name": "Telecaller RnR Report",
        "url": "/reports/telecaller-rnr/",
        "template": "reports/telecaller_rnr_report.html",
        "view": "leads.views.telecaller_rnr_report",
    },
    {
        "id": 17,
        "name": "Finance Dashboard",
        "url": "/finance/dashboard/",
        "template": "finance/dashboard.html",
        "view": "finance.views.dashboard",
    },
    {
        "id": 18,
        "name": "Receptionist Dashboard",
        "url": "/receptionist/dashboard/",
        "template": "receptionist/dashboard.html",
        "view": "leads.views.receptionist_dashboard",
    },
]

for p in pages:
    tmpl_path = os.path.join(templates_dir, p["template"])
    if not os.path.exists(tmpl_path):
        print(f"ERROR: {tmpl_path} does not exist!")
        continue
    with open(tmpl_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Find drawer or smart popover elements
    has_drawer = "date-drawer" in html or "drawer-toggle" in html or "data-date-drawer" in html
    has_smart_popover = "tp-smart-date-container" in html or "smart_calendar" in html

    # Look for input names
    input_names = re.findall(r'<input[^>]+name=["\']([^"\']+)["\']', html)
    date_inputs = [n for n in input_names if any(k in n for k in ["date", "from", "to", "start", "end"])]

    # Check data-from-name and data-to-name if present
    data_from = re.findall(r'data-from-name=["\']([^"\']+)["\']', html)
    data_to = re.findall(r'data-to-name=["\']([^"\']+)["\']', html)

    # Check for preset/period parameter
    period_matches = re.findall(r'name=["\'](period|range|preset)["\']', html)

    print(f"[{p['id']}] {p['name']}")
    print(f"     URL: {p['url']}")
    print(f"     Template: {p['template']}")
    print(f"     Date Inputs: {date_inputs}")
    print(f"     Data-from/to: {data_from} / {data_to}")
    print(f"     Preset Params: {period_matches}")
    print(f"     Current Mechanism: drawer={has_drawer}, smart_popover={has_smart_popover}")
    print()
