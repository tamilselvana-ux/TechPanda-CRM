import os, sys
sys.path.insert(0, os.path.abspath('CRM_Integrated_v2/CRM'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()
client = Client()

print("--- Testing Public & Authentication Pages ---")
pages_to_test = [
    ('/login/', 'Sign In - DigiPanda CRM'),
    ('/admin/login/', 'Admin Portal Login - DigiPanda CRM'),
    ('/manager/login/', 'Sales Head Login - DigiPanda CRM'),
    ('/telecaller/login/', 'Telecaller Login - DigiPanda CRM'),
    ('/finance/login/', 'Finance Portal Sign In - DigiPanda CRM'),
]

for url, expected_title in pages_to_test:
    resp = client.get(url)
    assert resp.status_code == 200, f"Failed {url}: status {resp.status_code}"
    content = resp.content.decode('utf-8')
    assert expected_title in content, f"Missing title '{expected_title}' in {url}"
    assert 'digipanda_symbol.png' in content or 'digipanda_logo.png' in content, f"Missing logo in {url}"
    print(f"PASS: {url} -> 200 OK, '{expected_title}', 'd' logo verified.")

print("\n--- Testing Authenticated Pages (Admin) ---")
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.filter(role='admin').first()

if admin_user:
    client.force_login(admin_user)
    auth_pages = [
        reverse('admin_dashboard'),
        reverse('admin_leads_list'),
        reverse('accountant_dashboard'),
        reverse('admin_walkin_forms_list'),
        reverse('admin_pipeline_statuses'),
    ]
    for url in auth_pages:
        resp = client.get(url)
        assert resp.status_code == 200, f"Failed auth page {url}: {resp.status_code}"
        content = resp.content.decode('utf-8')
        assert 'DigiPanda CRM' in content or 'digipanda' in content, f"Missing brand in {url}"
        assert 'digipanda_symbol.png' in content, f"Missing digipanda_symbol in sidebar of {url}"
        print(f"PASS: {url} -> 200 OK, 'd' logo in sidebar verified.")

print("\n--- Testing Static Asset Existence & Non-Zero Size ---")
from django.conf import settings
static_images = [
    'digipanda_symbol.png',
    'digipanda_symbol.svg',
    'digipanda_logo.png',
    'digipanda_logo_dark.png',
    'digipanda_logo.svg',
    'digipanda_logo_dark.svg',
    'favicon.png',
    'favicon.ico',
]

for img_name in static_images:
    p = os.path.join(settings.BASE_DIR, 'static', 'images', img_name)
    assert os.path.exists(p), f"Asset missing: {p}"
    size = os.path.getsize(p)
    assert size > 100, f"Asset too small ({size} bytes): {p}"
    print(f"PASS: {img_name} exists ({size:,} bytes)")

print("\nALL BRANDING VERIFICATION TESTS PASSED SUCCESSFULLY!")
