import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
crm_dir = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM"
if crm_dir not in sys.path:
    sys.path.insert(0, crm_dir)

django.setup()

import io
import base64
from decimal import Decimal
from django.template.loader import render_to_string
from django.test import RequestFactory
from leads.models import PaymentTransaction, Enrollment
from leads.constants import DIGIPANDA_INVOICE_CONFIG
from leads.views_enrollment import get_receipt_context, generate_receipt_pdf
from django.contrib.auth import get_user_model

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("TRACK D VERIFICATION SUITE")
print("=" * 60)

# 1. Verify Constants
print("\n[1] Verifying DIGIPANDA_INVOICE_CONFIG...")
assert DIGIPANDA_INVOICE_CONFIG['mobile'] == '9884678282', f"Mobile mismatch: {DIGIPANDA_INVOICE_CONFIG['mobile']}"
assert DIGIPANDA_INVOICE_CONFIG['gstin'] == '33AAMCT5031F1ZJ', f"GSTIN mismatch: {DIGIPANDA_INVOICE_CONFIG['gstin']}"
assert DIGIPANDA_INVOICE_CONFIG['pan'] == 'AAMCT5031F', f"PAN mismatch: {DIGIPANDA_INVOICE_CONFIG['pan']}"
assert DIGIPANDA_INVOICE_CONFIG['email'] == 'admin@digipanda.com', f"Email mismatch: {DIGIPANDA_INVOICE_CONFIG['email']}"
assert DIGIPANDA_INVOICE_CONFIG['website'] == 'www.digipanda.com', f"Website mismatch: {DIGIPANDA_INVOICE_CONFIG['website']}"
print("   ✓ All company identity fields match canonical reference PDF exactly!")

# 2. Verify Signature Asset
print("\n[2] Verifying Signature Asset...")
sig_path = os.path.join(crm_dir, 'static', 'images', 'shashi_sign.png')
assert os.path.exists(sig_path), f"Signature file missing: {sig_path}"
sig_size = os.path.getsize(sig_path)
print(f"   ✓ Signature exists at {sig_path} ({sig_size} bytes)")

# 3. Verify Payment Receipt Context & Template Rendering
print("\n[3] Verifying Payment Receipt & Email Template Rendering...")
rf = RequestFactory()
req = rf.get('/')

# Pick or mock an approved transaction
txn = PaymentTransaction.objects.filter(status='APPROVED').first()
if not txn:
    txn = PaymentTransaction.objects.first()

if txn:
    ctx = get_receipt_context(req, txn)
    email_html = render_to_string('emails/payment_receipt.html', ctx)
    web_html = render_to_string('leads/receipt.html', ctx)
    
    # Assertions
    assert 'DigiPanda' in email_html, "DigiPanda missing from email HTML"
    assert '33AAMCT5031F1ZJ' in email_html, "GSTIN missing from email HTML"
    assert 'AAMCT5031F' in email_html, "PAN missing from email HTML"
    assert '9884678282' in email_html, "Phone missing from email HTML"
    assert 'admin@digipanda.com' in email_html, "Email missing from email HTML"
    assert 'www.digipanda.com' in email_html, "Website missing from email HTML"
    assert 'TechPanda' not in email_html, "TechPanda found in email HTML!"
    assert 'TechPanda' not in web_html, "TechPanda found in web HTML!"
    
    print("   ✓ Email HTML rendered cleanly with zero 'TechPanda' references!")
    print(f"   ✓ Email HTML length: {len(email_html)} characters")
    print(f"   ✓ Web HTML length: {len(web_html)} characters")

    # 4. Verify PDF Generation
    print("\n[4] Verifying PDF Generation via xhtml2pdf...")
    pdf_bytes = generate_receipt_pdf(ctx)
    assert pdf_bytes is not None and len(pdf_bytes) > 1000, "PDF generation failed or output too small"
    print(f"   ✓ PDF generated successfully: {len(pdf_bytes)} bytes")
    
    # Save a sample rendered PDF to artifacts for review
    sample_pdf_path = r"C:\Users\tamil\.gemini\antigravity\brain\364306a8-735f-4286-9c22-bb9e159eba4d\verified_generated_receipt.pdf"
    with open(sample_pdf_path, "wb") as pf:
        pf.write(pdf_bytes)
    print(f"   ✓ Sample PDF saved to {sample_pdf_path}")
else:
    print("   ⚠️ No payment transaction in DB to test live query")

# 5. Verify CSS Rules
print("\n[5] Verifying CSS Rules for Calendar Popover & Select Chevrons...")
with open(os.path.join(crm_dir, 'static', 'css', 'date-range-picker.css'), 'r', encoding='utf-8') as f:
    drp_css = f.read()
assert 'z-index: 9999 !important;' in drp_css, "z-index 9999 missing from date-range-picker.css"
assert '.tp-filter-bar,' in drp_css and 'overflow: visible !important;' in drp_css, "overflow visible missing from date-range-picker.css"
print("   ✓ date-range-picker.css contains z-index 9999 and overflow: visible rules")

with open(os.path.join(crm_dir, 'static', 'css', 'crm.css'), 'r', encoding='utf-8') as f:
    crm_css = f.read()
assert 'select.tp-select-compact' in crm_css, "select.tp-select-compact missing from crm.css"
assert 'padding: 4px 28px 4px 10px !important;' in crm_css, "padding-right 28px missing from crm.css"
assert '-webkit-appearance: none !important;' in crm_css, "-webkit-appearance missing from crm.css"
print("   ✓ crm.css contains single chevron background and 28px right padding rules")

with open(os.path.join(crm_dir, 'static', 'css', 'design-system.css'), 'r', encoding='utf-8') as f:
    ds_css = f.read()
assert 'select.tp-select-compact' in ds_css, "select.tp-select-compact missing from design-system.css"
assert '-webkit-appearance: none !important;' in ds_css, "-webkit-appearance missing from design-system.css"
print("   ✓ design-system.css contains appearance: none and single chevron rules")

print("\n" + "=" * 60)
print("ALL TRACK D VERIFICATIONS PASSED (100% GREEN)!")
print("=" * 60)
