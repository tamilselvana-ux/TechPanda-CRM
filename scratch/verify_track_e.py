import os
import sys
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
crm_dir = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM"
if crm_dir not in sys.path:
    sys.path.insert(0, crm_dir)

django.setup()

from django.template.loader import render_to_string
from django.utils import timezone

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("TRACK E VERIFICATION SUITE")
print("=" * 60)

# 1. Test enrollment_confirmation.html rendering
print("\n[1] Verifying Enrollment Welcome Email Template...")
enroll_ctx = {
    'student_name': 'Deepak Roshan',
    'student_id': 'STU-12519',
    'enrollment_number': 'ENR-2026-0042',
    'course_name': 'Full Stack Data Science & AI',
    'branch_name': 'Main Campus / Corporate HQ',
    'enrollment_date': timezone.now(),
    'session': '2026 - 2027',
    'campus_address': 'DigiPanda Towers, Knowledge Park, OMR, Chennai, Tamil Nadu - 600096',
    'logo_data_uri': '',
}
enroll_out = render_to_string('emails/enrollment_confirmation.html', enroll_ctx)
assert 'techpanda' not in enroll_out.lower(), "techpanda found in enrollment_confirmation.html!"
assert '98846' in enroll_out, "Updated phone missing in enrollment_confirmation.html!"
assert 'admin@digipanda.com' in enroll_out, "admin@digipanda.com missing in enrollment_confirmation.html!"
print("   ✓ enrollment_confirmation.html rendered cleanly without any legacy branding!")
print(f"   ✓ Length: {len(enroll_out)} characters")

# 2. Test installment_reminder.html rendering
print("\n[2] Verifying Installment Reminder Email Template...")
remind_ctx = {
    'student_name': 'Deepak Roshan',
    'student_id': 'STU-12519',
    'enrollment_number': 'ENR-2026-0042',
    'course_name': 'Full Stack Data Science & AI',
    'branch_name': 'Main Campus / Corporate HQ',
    'installment_number': 2,
    'total_installments': 3,
    'due_date': timezone.now().date(),
    'due_amount': Decimal('15000.00'),
    'balance_amount': Decimal('25000.00'),
    'total_fee': Decimal('40000.00'),
    'pill_text': 'Due in 3 Days',
    'headline': 'Upcoming Fee Installment',
    'payment_url': 'https://pay.digipanda.com/pay/ENR-0042',
    'accounts_phone': '+91 98846 78282',
    'accounts_email': 'admin@digipanda.com',
}
remind_out = render_to_string('emails/installment_reminder.html', remind_ctx)
assert 'techpanda' not in remind_out.lower(), "techpanda found in installment_reminder.html!"
assert '50200115357040' in remind_out, "HDFC account number missing in installment_reminder.html!"
assert 'HDFC0000141' in remind_out, "IFSC missing in installment_reminder.html!"
print("   ✓ installment_reminder.html rendered cleanly with direct bank transfer instructions!")
print(f"   ✓ Length: {len(remind_out)} characters")

# 3. Verify 3D Cinematic assets
print("\n[3] Verifying 3D Cinematic Assets...")
css_3d = os.path.join(crm_dir, 'static', 'css', 'modern-3d-cinematic.css')
js_3d = os.path.join(crm_dir, 'static', 'js', 'modern-3d-cinematic.js')
assert os.path.exists(css_3d), "modern-3d-cinematic.css is missing!"
assert os.path.exists(js_3d), "modern-3d-cinematic.js is missing!"
print(f"   ✓ modern-3d-cinematic.css: {os.path.getsize(css_3d)} bytes")
print(f"   ✓ modern-3d-cinematic.js: {os.path.getsize(js_3d)} bytes")

# 4. Verify Plan file
print("\n[4] Verifying Meta Leads Separation Plan...")
plan_path = os.path.join(crm_dir, 'docs', 'plan_meta_leads_facebook_vs_instagram.md')
assert os.path.exists(plan_path), "Meta plan document missing!"
print(f"   ✓ plan_meta_leads_facebook_vs_instagram.md: {os.path.getsize(plan_path)} bytes")

print("\n" + "=" * 60)
print("ALL TRACK E VERIFICATIONS PASSED (100% GREEN)!")
print("=" * 60)
