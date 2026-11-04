import os, sys
from decimal import Decimal
sys.path.insert(0, r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import Client
from accounts.models import User
from leads.models import Lead
from leads.models_enrollment import Enrollment, GSTTreatment
from products.models import Product

print("1. Testing Server-side Pure Decimal calculate_gst_breakdown for 35,000.00 With GST...")
res_with = Enrollment.calculate_gst_breakdown(Decimal('35000.00'), GSTTreatment.WITH_GST, Decimal('18.00'))
print("Result With GST:", res_with)
assert res_with['total_payable'] == Decimal('35000.00'), f"Expected total 35000.00, got {res_with['total_payable']}"
assert res_with['taxable_amount'] == Decimal('29661.02'), f"Expected taxable 29661.02, got {res_with['taxable_amount']}"
assert res_with['tax_amount'] == Decimal('5338.98'), f"Expected tax 5338.98, got {res_with['tax_amount']}"
assert res_with['taxable_amount'] + res_with['tax_amount'] == res_with['total_payable']
print("[PASS] 35000.00 With GST gives total 35,000.00 (not 41,300.00)!")

print("\n2. Testing Server-side Pure Decimal calculate_gst_breakdown for 35,000.00 Without GST...")
res_without = Enrollment.calculate_gst_breakdown(Decimal('35000.00'), GSTTreatment.WITHOUT_GST, Decimal('18.00'))
print("Result Without GST:", res_without)
assert res_without['total_payable'] == Decimal('35000.00'), f"Expected total 35000.00, got {res_without['total_payable']}"
assert res_without['taxable_amount'] == Decimal('35000.00'), f"Expected taxable 35000.00, got {res_without['taxable_amount']}"
assert res_without['tax_amount'] == Decimal('0.00'), f"Expected tax 0.00, got {res_without['tax_amount']}"
print("[PASS] 35000.00 Without GST gives total 35,000.00 with 0 tax!")

print("\n3. Testing JSON API /enrollments/api/calculate-gst/ for 35000.00 With GST...")
admin_user = User.objects.filter(is_superuser=True).first() or User.objects.filter(role='ADMIN').first()
client = Client()
client.force_login(admin_user)

api_resp = client.get('/enrollments/api/calculate-gst/?base_course_fee=35000.00&gst_treatment=WITH_GST&tax_rate=18.00')
assert api_resp.status_code == 200
api_data = api_resp.json()
print("API Data:", api_data)
assert api_data['success'] is True
assert float(api_data['total_payable']) == 35000.00, f"Expected 35000.00, got {api_data['total_payable']}"
assert float(api_data['taxable_amount']) == 29661.02, f"Expected 29661.02, got {api_data['taxable_amount']}"
assert float(api_data['tax_amount']) == 5338.98, f"Expected 5338.98, got {api_data['tax_amount']}"
print("[PASS] JSON API returned exactly 35,000.00 total payable!")

print("\n4. Testing /leads/<id>/enroll/ course select option text...")
lead = Lead.objects.first()
page_resp = client.get(f'/leads/{lead.id}/enroll/')
assert page_resp.status_code == 200
html = page_resp.content.decode('utf-8')

# Ensure option text contains clean course name, not appended price
prod = Product.objects.filter(status='Active').first()
if prod:
    clean_option = f'>{prod.name}</option>'
    assert clean_option in html, f"Expected clean option '{clean_option}' in HTML"
    assert f'data-price="{prod.price:.2f}"' in html, "data-price missing from option"
    assert f'data-gst="{prod.gst_treatment}"' in html, "data-gst missing from option"
    print(f"[PASS] Course option renders cleanly: '{clean_option}' with background data-price and data-gst!")

print("\n==========================================")
print("ALL TRACK N TESTS PASSED WITH 100% SUCCESS!")
print("==========================================")
