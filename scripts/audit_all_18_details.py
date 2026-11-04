import sys, os
sys.path.insert(0, r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.urls import resolve
import inspect

urls = [
    ("/admin/dashboard/", "admin_dashboard/dashboard.html"),
    ("/accountant/dashboard/", "accountant/dashboard.html"),
    ("/accountant/verification/", "accountant/verification_list.html"),
    ("/admin/leads/", "admin/leads_list.html"),
    ("/admin/leads/new/", "admin/new_leads_list.html"),
    ("/manager/branch-head/dashboard/", "branch_head_dashboard/dashboard.html"),
    ("/counselor/dashboard/", "counselor_dashboard/dashboard.html"),
    ("/manager/dashboard/", "manager_dashboard/dashboard.html"),
    ("/telecaller/dashboard/", "telecaller_dashboard/dashboard.html"),
    ("/admin/calls/", "admin/calls_list.html"),
    ("/call-recordings/recordings/", "calls/recordings_list.html"),
    ("/admin/followups/", "admin/followups_list.html"),
    ("/counselor/followups/", "counselor/followups_list.html"),
    ("/admin/reports/", "reports/admin_reports.html"),
    ("/manager/reports/", "reports/dashboard_report.html"),
    ("/reports/telecaller-rnr/", "reports/telecaller_rnr_report.html"),
    ("/finance/dashboard/", "finance/dashboard.html"),
    ("/receptionist/dashboard/", "receptionist/dashboard.html"),
]

for idx, (u, tmpl) in enumerate(urls, 1):
    m = resolve(u)
    fn = m.func
    mod = fn.__module__
    name = fn.__name__
    source = inspect.getsource(fn)
    lines = source.splitlines()

    # Search for date parameters
    date_get_lines = [l.strip() for l in lines if "GET.get" in l and any(k in l for k in ["date", "from", "to", "period", "range"])]
    has_norm = any("extract_normalized_date_range" in l for l in lines)
    has_export = any("export" in l.lower() for l in lines)
    has_page = any("page" in l for l in lines)
    
    print(f"[{idx}] {u}")
    print(f"    View: {mod}.{name}")
    print(f"    Uses extract_normalized_date_range: {has_norm}")
    print(f"    GET params: {date_get_lines}")
    print(f"    Has export: {has_export}, Has pagination: {has_page}")
    print()
