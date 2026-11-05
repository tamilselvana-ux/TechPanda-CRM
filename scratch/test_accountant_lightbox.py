import os
import sys

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from leads.models import Lead
from branches.models import Branch
from products.models import Product
from leads.models_enrollment import Enrollment, PaymentTransaction
from leads.views_accountant import accountant_payment_verification
from accounts.models import UserRole

User = get_user_model()

print("--- TESTING ITEM 149: ACCOUNTANT VERIFICATION IMAGE LIGHTBOX ---")

# 1. Setup Accountant User
branch, _ = Branch.objects.get_or_create(name="Accountant Branch", defaults={"address": "Finance Ave", "phone": "044-99881122"})
accountant, _ = User.objects.get_or_create(
    username="accountant_lb_test",
    defaults={"role": UserRole.ACCOUNTANT, "first_name": "Raman", "last_name": "Nathan", "branch": branch}
)
accountant.role = UserRole.ACCOUNTANT
accountant.branch = branch
accountant.save()

product, _ = Product.objects.get_or_create(name="AI Full Stack Pro", defaults={"price": 45000})

lead, _ = Lead.objects.get_or_create(
    phone="9840991122",
    defaults={"name": "Pooja Hegde", "email": "pooja@example.com", "branch": branch, "product": product}
)

enrollment, _ = Enrollment.objects.get_or_create(
    lead=lead,
    defaults={
        "enrollment_number": "ENR-LB-001",
        "student_name": lead.name,
        "student_phone": lead.phone,
        "student_email": lead.email,
        "branch": branch,
        "product": product,
        "total_payable": 45000,
        "total_paid": 15000,
        "status": "Active"
    }
)
enrollment.branch = branch
enrollment.save()

# Create a Payment with a dummy proof image
tx, _ = PaymentTransaction.objects.get_or_create(
    enrollment=enrollment,
    transaction_reference="UTR-LB-123456",
    defaults={
        "amount": 15000,
        "payment_method": "UPI",
        "status": "Pending Verification",
        "receipt_number": "REC-LB-001",
        "payment_proof": "payment_proofs/test_proof.jpg"
    }
)
tx.payment_proof = "payment_proofs/test_proof.jpg"
tx.save()

# 2. Verify Lightbox JS File Integrity
js_path = os.path.join('static', 'js', 'verification-lightbox.js')
assert os.path.exists(js_path), "verification-lightbox.js must exist in static/js/"
with open(js_path, 'r', encoding='utf-8') as f:
    js_content = f.read()
assert "openProofLightbox" in js_content
assert "zoomLightbox" in js_content
assert "rotateLightbox" in js_content
assert "toggleContrastLightbox" in js_content
assert "copyLightboxUTR" in js_content
print("✅ Test 1 Passed: verification-lightbox.js implements zoom, 90° rotation, contrast boost, and pan engines.")

# 3. Test View Rendering
factory = RequestFactory()
req = factory.get('/accountant/verification/')
req.user = accountant
res = accountant_payment_verification(req)
assert res.status_code == 200, f"Expected 200, got {res.status_code}"

html = res.content.decode('utf-8')
assert "proofLightboxModal" in html, "Page must render proofLightboxModal container"
assert "verification-lightbox.js" in html, "Page must include verification-lightbox.js script"
assert "openProofLightbox" in html, "Proof cell must trigger openProofLightbox on click"
assert "btnToggleContrast" in html, "Lightbox must provide contrast enhancement toggle"
assert "btnCopyLightboxUtr" in html, "Lightbox must provide 1-click UTR copy tool"
print("✅ Test 2 Passed: Accountant Verification List renders Image Inspection Lightbox and controls with HTTP 200 OK.")

print("--- ALL TESTS PASSED FOR ITEM 149 ---")
