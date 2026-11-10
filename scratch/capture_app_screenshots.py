import os
import sys
import subprocess
import django

sys.path.insert(0, r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

ASSETS_DIR = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\docs\assets"
os.makedirs(ASSETS_DIR, exist_ok=True)
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

User = get_user_model()
admin_user = User.objects.filter(role__in=["ADMIN", "superadmin"]).first() or User.objects.filter(is_superuser=True).first()
counselor_user = User.objects.filter(role__in=["COUNSELOR", "counselor"]).first()
accountant_user = User.objects.filter(role__in=["ACCOUNTANT", "accountant"]).first()

PAGES_TO_CAPTURE = [
    ("screenshot_leads_dashboard.png", "/admin/leads/", admin_user, "Admin Leads Pipeline & Kanban Desk"),
    ("screenshot_counselor_workbench.png", "/counselor/dashboard/", counselor_user, "Counselor Daily Workbench & Lead Pipeline"),
    ("screenshot_finance_dashboard.png", "/finance/dashboard/", accountant_user, "Finance Ledger & Accounting Dashboard"),
    ("screenshot_whatsapp_inbox.png", "/whatsapp/", admin_user, "Meta WhatsApp Omnichannel Inbox & 24h Window"),
    ("screenshot_duplicate_leads.png", "/admin/duplicate-leads/", admin_user, "Duplicate Leads Verification Desk & UTR Shield"),
]

def capture_pages():
    for filename, url, user, title in PAGES_TO_CAPTURE:
        out_png = os.path.join(ASSETS_DIR, filename)
        client = Client()
        if user:
            client.force_login(user)
        try:
            resp = client.get(url, follow=True)
            print(f"Fetching {url} -> Status: {resp.status_code}")
            if resp.status_code == 200:
                html = resp.content.decode("utf-8", errors="ignore")
                # Route static assets to dev server
                html = html.replace('href="/static/', 'href="http://127.0.0.1:8001/static/')
                html = html.replace('src="/static/', 'src="http://127.0.0.1:8001/static/')
                # Add base tag
                if "<head>" in html:
                    html = html.replace("<head>", '<head><base href="http://127.0.0.1:8001/">')

                temp_html = os.path.join(ASSETS_DIR, f"temp_{filename}.html")
                with open(temp_html, "w", encoding="utf-8") as f:
                    f.write(html)

                cmd = [
                    CHROME_PATH,
                    "--headless=new",
                    "--disable-gpu",
                    "--window-size=1280,800",
                    f"--screenshot={out_png}",
                    temp_html
                ]
                subprocess.run(cmd, capture_output=True)
                if os.path.exists(temp_html):
                    os.remove(temp_html)
                if os.path.exists(out_png):
                    print(f"  [SUCCESS] Captured {filename} ({os.path.getsize(out_png)} bytes) - {title}")
                else:
                    print(f"  [FAIL] Chrome did not write {filename}")
            else:
                print(f"  [WARN] Page {url} returned status {resp.status_code}")
        except Exception as e:
            print(f"  [ERROR] Capturing {url}: {e}")

if __name__ == "__main__":
    capture_pages()
