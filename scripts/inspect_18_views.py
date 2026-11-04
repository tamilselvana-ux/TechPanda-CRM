import os
import sys

base_dir = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM"
sys.path.insert(0, base_dir)

# Detailed inspection of each of the 18 views
import inspect
from django.conf import settings
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import leads.views as lv
import accounts.views as av
import calls.views as cv
import finance.views as fv

views_map = {
    "1. Admin Dashboard": lv.admin_dashboard,
    "2. Accountant Dashboard": av.accountant_dashboard,
    "3. Accountant Verification": av.verification_list,
    "4. Admin Leads List": lv.leads_list,
    "5. Admin New Leads List": lv.new_leads_list,
    "6. Branch Head Dashboard": lv.branch_head_dashboard,
    "7. Counselor Dashboard": lv.counselor_dashboard,
    "8. Manager Dashboard": lv.manager_dashboard,
    "9. Telecaller Dashboard": lv.telecaller_dashboard,
    "10. Admin Calls List": cv.calls_list,
    "11. Call Recordings List": cv.recordings_list,
    "12. Admin Followups List": lv.admin_followups_list,
    "13. Counselor Followups List": lv.counselor_followups_list,
    "14. Admin Reports": lv.admin_reports,
    "15. Manager Reports": lv.manager_reports,
    "16. Telecaller RnR Report": lv.telecaller_rnr_report,
    "17. Finance Dashboard": fv.dashboard,
    "18. Receptionist Dashboard": lv.receptionist_dashboard,
}

for name, fn in views_map.items():
    src = inspect.getsource(fn)
    lines = [l.strip() for l in src.splitlines()]
    date_lines = [l for l in lines if any(k in l for k in ["date_from", "from_date", "start_date", "period", "range", "extract_normalized_date_range", "parse_iso_date"])]
    print(f"=== {name} ===")
    for dl in date_lines[:8]:
        print("  ", dl)
    print()
