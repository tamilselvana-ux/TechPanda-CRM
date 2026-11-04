import os, re

CRM_ROOT = 'CRM_Integrated_v2/CRM'
check_list = [
    'templates/admin_dashboard/dashboard.html',
    'templates/counselor/leads_list.html',
    'templates/manager/leads_list.html',
    'templates/telecaller/leads_list.html',
    'templates/admin/walkin_forms_list.html',
    'templates/reports/dashboard_report.html',
    'templates/reports/manager_reports.html',
    'templates/admin/enrolled_students.html',
    'templates/leads/enrolled_students.html',
    'templates/admin/email_logs_list.html',
    'templates/chat/campaigns/campaigns_list.html',
    'templates/fb_leads/leads.html',
]

for rel in check_list:
    fpath = os.path.join(CRM_ROOT, rel)
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            txt = f.read()
        date_inputs = re.findall(r'<input[^>]*type=[\'"]date[\'"][^>]*>', txt, re.IGNORECASE)
        date_names = re.findall(r'name=[\'"]([^\'"]*(?:date|from|to|period)[^\'"]*)[\'"]', txt, re.IGNORECASE)
        date_mentions = 'date' in txt.lower()
        print(f"{rel}: date_inputs={len(date_inputs)}, date_names={date_names}")
    else:
        print(f"{rel}: DOES NOT EXIST")
