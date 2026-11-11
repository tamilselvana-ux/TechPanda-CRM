import os, re, sys, subprocess, django
sys.path.insert(0, r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from leads.models import Lead

ASSETS_DIR = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\docs\assets"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
STATIC_URI = "file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/static/"

User = get_user_model()
admin_user = User.objects.filter(role="ADMIN", is_active=True).first() or User.objects.filter(is_superuser=True).first()
lead_id = Lead.objects.first().pk if Lead.objects.exists() else 1

EXTRA_PAGES = [
    ("ui_lead_enroll.png", f"/leads/{lead_id}/enroll/", admin_user),
    ("ui_walkin_form_public.png", "/enquiry/", None),
    ("ui_whatsapp_campaigns.png", "/whatsapp/campaigns/", admin_user),
    ("ui_admin_telecallers.png", "/admin/telecallers/", admin_user),
]

def scrub_pii(html_str):
    html_str = re.sub(r'(/static/[^"\'\s?]+)\?[^"\'\s]*', r'\1', html_str)
    html_str = html_str.replace('href="/static/', f'href="{STATIC_URI}')
    html_str = html_str.replace("href='/static/", f"href='{STATIC_URI}")
    html_str = html_str.replace('src="/static/', f'src="{STATIC_URI}')
    html_str = html_str.replace("src='/static/", f"src='{STATIC_URI}")
    html_str = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'priya.s@example.com', html_str)
    html_str = re.sub(r'\+91[\s-]?[6-9]\d{9}', '+91 98xxxxxx10', html_str)
    html_str = re.sub(r'(?<![\d/=-])[6-9]\d{9}(?![\d])', '98xxxxxx10', html_str)
    return html_str

for filename, url, user in EXTRA_PAGES:
    out_png = os.path.join(ASSETS_DIR, filename)
    client = Client()
    if user:
        client.force_login(user)
    resp = client.get(url, follow=True)
    if resp.status_code == 200:
        html = scrub_pii(resp.content.decode("utf-8", errors="ignore"))
        temp_html = os.path.join(ASSETS_DIR, f"_tmp_{filename}.html")
        with open(temp_html, "w", encoding="utf-8") as f:
            f.write(html)
        cmd = [CHROME_PATH, "--headless=new", "--disable-gpu", "--allow-file-access-from-files", "--virtual-time-budget=2000", "--window-size=1280,820", f"--screenshot={out_png}", temp_html]
        subprocess.run(cmd, capture_output=True)
        if os.path.exists(temp_html):
            os.remove(temp_html)
        print(f"[200] {filename} -> {os.path.getsize(out_png)//1024} KB")
    else:
        print(f"[{resp.status_code}] SKIPPED {url}")
