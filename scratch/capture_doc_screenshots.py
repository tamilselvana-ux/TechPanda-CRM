import os
import re
import sys
import shutil
import subprocess
import django

sys.path.insert(0, r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from leads.models import Lead

ASSETS_DIR = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\docs\assets"
os.makedirs(ASSETS_DIR, exist_ok=True)
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
STATIC_URI = "file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/static/"

# Copy crisp circular logo
src_logo = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\static\images\itechpanda_symbol.png"
if os.path.exists(src_logo):
    shutil.copy2(src_logo, os.path.join(ASSETS_DIR, "logo.png"))

User = get_user_model()
admin_user = User.objects.filter(role="ADMIN", is_active=True).first() or User.objects.filter(is_superuser=True).first()
branch_head_user = User.objects.filter(role="BRANCH_HEAD", is_active=True).first()
counselor_user = User.objects.filter(role="COUNSELOR", is_active=True).first()
telecaller_user = User.objects.filter(role="TELECALLER", is_active=True).first()
receptionist_user = User.objects.filter(role="RECEPTIONIST", is_active=True).first()
accountant_user = User.objects.filter(role="ACCOUNTANT", is_active=True).first()
finance_user = User.objects.filter(role="FINANCE_HEAD", is_active=True).first()

sample_lead = Lead.objects.first()
lead_id = sample_lead.pk if sample_lead else 1

PAGES = [
    ("ui_login.png", "/login/", None),
    ("ui_admin_dashboard.png", "/admin/dashboard/", admin_user),
    ("ui_admin_leads.png", "/admin/leads/", admin_user),
    ("ui_leads_kanban.png", "/leads/kanban/", admin_user),
    ("ui_telecaller_dashboard.png", "/telecaller/dashboard/", telecaller_user),
    ("ui_telecaller_leads.png", "/telecaller/leads/", telecaller_user),
    ("ui_lead_detail.png", f"/admin/leads/{lead_id}/", admin_user),
    ("ui_counselor_dashboard.png", "/counselor/dashboard/", counselor_user),
    ("ui_followups_list.png", "/admin/followups/", admin_user),
    ("ui_missed_calls.png", "/calls/missed/", admin_user),
    ("ui_call_recordings.png", "/call-recordings/", admin_user),
    ("ui_receptionist_desk.png", "/receptionist/dashboard/", receptionist_user),
    ("ui_walkin_qr_standee.png", "/receptionist/qr-standee/", receptionist_user),
    ("ui_branch_head_dashboard.png", "/manager/branch-head/dashboard/", branch_head_user),
    ("ui_lead_allocation_setup.png", "/admin/settings/lead-setup/", admin_user),
    ("ui_reports_rnr.png", "/reports/telecaller-rnr/", admin_user),
    ("ui_admin_reports.png", "/admin/reports/", admin_user),
    ("ui_accountant_verification.png", "/accountant/verification/", accountant_user),
    ("ui_finance_dashboard.png", "/finance/dashboard/", finance_user),
    ("ui_fb_leads.png", "/facebook-leads/", admin_user),
    ("ui_fb_accounts.png", "/facebook-leads/accounts/", admin_user),
    ("ui_whatsapp_inbox.png", "/whatsapp/", admin_user),
    ("ui_user_profile.png", "/profile/", admin_user),
]

def scrub_pii(html_str):
    # Remove query-string cache busters on local CSS/JS so file:/// URLs load cleanly
    html_str = re.sub(r'(/static/[^"\'\s?]+)\?[^"\'\s]*', r'\1', html_str)
    # Point all /static/ references directly to disk static files
    html_str = html_str.replace('href="/static/', f'href="{STATIC_URI}')
    html_str = html_str.replace("href='/static/", f"href='{STATIC_URI}")
    html_str = html_str.replace('src="/static/', f'src="{STATIC_URI}')
    html_str = html_str.replace("src='/static/", f"src='{STATIC_URI}")
    # Mask emails & phone numbers in visible HTML
    html_str = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'priya.s@example.com', html_str)
    html_str = re.sub(r'\+91[\s-]?[6-9]\d{9}', '+91 98xxxxxx10', html_str)
    html_str = re.sub(r'(?<![\d/=-])[6-9]\d{9}(?![\d])', '98xxxxxx10', html_str)
    return html_str

def capture_all():
    for filename, url, user in PAGES:
        out_png = os.path.join(ASSETS_DIR, filename)
        client = Client()
        if user:
            client.force_login(user)
        try:
            resp = client.get(url, follow=True)
            if resp.status_code == 200:
                html = resp.content.decode("utf-8", errors="ignore")
                html = scrub_pii(html)
                temp_html = os.path.join(ASSETS_DIR, f"_tmp_{filename}.html")
                with open(temp_html, "w", encoding="utf-8") as f:
                    f.write(html)
                cmd = [
                    CHROME_PATH,
                    "--headless=new",
                    "--disable-gpu",
                    "--allow-file-access-from-files",
                    "--virtual-time-budget=2000",
                    "--window-size=1280,820",
                    f"--screenshot={out_png}",
                    temp_html
                ]
                subprocess.run(cmd, capture_output=True)
                if os.path.exists(temp_html):
                    os.remove(temp_html)
                size_kb = os.path.getsize(out_png) // 1024 if os.path.exists(out_png) else 0
                print(f"[200] {filename:<32} -> {size_kb} KB")
            else:
                print(f"[{resp.status_code}] SKIPPED {url}")
        except Exception as e:
            print(f"[ERR] {url}: {e}")

if __name__ == "__main__":
    capture_all()
