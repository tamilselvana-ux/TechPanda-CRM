import os, sys
sys.path.insert(0, r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import Client
from accounts.models import User
from products.models import Product
from leads.models import Lead
from branches.models import Branch
from leads.models_enrollment import Enrollment

admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.filter(role='ADMIN').first()

print("Using admin user:", admin_user.email)
client = Client()
client.force_login(admin_user)

# 1. Test GET /admin/products/
resp_list = client.get('/admin/products/')
assert resp_list.status_code == 200, f"Expected 200, got {resp_list.status_code}"
content = resp_list.content.decode('utf-8')
assert 'gst_treatment' in content, "gst_treatment form control missing from /admin/products/"
assert 'GST Option' in content, "GST Option label missing from /admin/products/"
print("[PASS] GET /admin/products/ rendered with GST Option field.")

# 2. Test POST /admin/products/ (create product with With GST)
prod_name = "Cloud Architecture Masterclass"
Product.objects.filter(name=prod_name).delete()

resp_create = client.post('/admin/products/', {
    'action': 'create',
    'name': prod_name,
    'description': 'AWS & GCP Certified Cloud Architect',
    'price': '42000.00',
    'gst_treatment': 'WITH_GST',
    'status': 'Active'
}, follow=True)
assert resp_create.status_code == 200

created_prod = Product.objects.filter(name=prod_name).first()
assert created_prod is not None, "Product was not created"
assert str(created_prod.price) == '42000.00', f"Price mismatch: {created_prod.price}"
assert created_prod.gst_treatment == 'WITH_GST', f"GST mismatch: {created_prod.gst_treatment}"
print(f"[PASS] Product '{created_prod.name}' created with price {created_prod.price} and GST {created_prod.gst_treatment}.")

# 3. Test POST /admin/products/<id>/edit/ (switch to Without GST)
resp_edit = client.post(f'/admin/products/{created_prod.id}/edit/', {
    'name': prod_name,
    'description': 'AWS & GCP Certified Cloud Architect (Updated)',
    'price': '38000.00',
    'gst_treatment': 'WITHOUT_GST',
    'status': 'Active'
}, follow=True)
assert resp_edit.status_code == 200

created_prod.refresh_from_db()
assert str(created_prod.price) == '38000.00', f"Price mismatch after edit: {created_prod.price}"
assert created_prod.gst_treatment == 'WITHOUT_GST', f"GST mismatch after edit: {created_prod.gst_treatment}"
print(f"[PASS] Product updated: fee = {created_prod.price}, GST = {created_prod.gst_treatment}.")

# 4. Test GET /leads/<id>/enroll/ contains data-price and data-gst on options
test_lead = Lead.objects.first()
resp_enroll = client.get(f'/leads/{test_lead.id}/enroll/')
assert resp_enroll.status_code == 200
enroll_html = resp_enroll.content.decode('utf-8')
assert 'data-price=' in enroll_html, "data-price missing from course select options"
assert 'data-gst=' in enroll_html, "data-gst missing from course select options"
assert 'applySelectedCourseData' in enroll_html, "applySelectedCourseData JavaScript missing"
assert 'id_enrolling_product' in enroll_html, "id_enrolling_product select id missing"
print("[PASS] /leads/<id>/enroll/ renders with data-price, data-gst, and dynamic auto-population listener.")

# 5. Clean up created product
created_prod.delete()
print("[PASS] Test product cleaned up.")

# 6. Check auto-filter.js does not contain keystroke auto-submit
with open(r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\static\js\auto-filter.js", 'r', encoding='utf-8') as f:
    js_code = f.read()

assert 'txt.addEventListener(\'input\'' not in js_code, "Unwanted input listener still present in auto-filter.js"
assert 'submitForm(txt)' in js_code, "Enter key submit missing from auto-filter.js"
print("[PASS] auto-filter.js correctly enforces Enter-only / Button-only submission with 0 keystroke interruptions.")

print("\n==========================================")
print("ALL TRACK M TESTS PASSED WITH 100% SUCCESS!")
print("==========================================")
