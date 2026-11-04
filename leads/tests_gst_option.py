from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from leads.models import Lead
from branches.models import Branch
from products.models import Product
from leads.models_enrollment import (
    Enrollment,
    GSTTreatment,
    PaymentPlan,
    PaymentTransaction,
    PaymentTransactionStatus,
    PaymentMethod,
)
from leads.views_enrollment import get_receipt_context

User = get_user_model()


class GSTOptionTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Test GST Branch", status=Branch.Status.ACTIVE)
        self.counselor = User.objects.create_user(
            username="counselor_gst_unique",
            password="testpassword123",
            role="counselor",
            branch=self.branch,
        )
        self.lead = Lead.objects.create(
            name="Ramesh Kumar",
            phone="9876501234",
            email="ramesh@example.com",
            branch=self.branch,
            assigned_counselor=self.counselor,
        )
        self.product = Product.objects.create(
            name="Full Stack Python Mastery Unique",
            price=Decimal("50000.00"),
            status="active",
        )
        self.factory = RequestFactory()

    def tearDown(self):
        PaymentTransaction.objects.filter(receipt_number__startswith="TP-NOGST").delete()
        Enrollment.objects.filter(enrollment_number__in=["ENR-NOGST-001", "ENR-LEGACY-001"]).delete()
        self.lead.delete()
        self.product.delete()
        self.counselor.delete()
        self.branch.delete()

    def test_with_gst_calculation(self):
        """CR-2: With GST computes 18% tax on top of base fee."""
        calc = Enrollment.calculate_gst_breakdown(
            base_fee=Decimal("50000.00"),
            treatment=GSTTreatment.WITH_GST,
            tax_rate=Decimal("18.00"),
        )
        self.assertEqual(calc["tax_rate"], Decimal("18.00"))
        self.assertEqual(calc["taxable_amount"], Decimal("50000.00"))
        self.assertEqual(calc["tax_amount"], Decimal("9000.00"))
        self.assertEqual(calc["total_payable"], Decimal("59000.00"))

    def test_without_gst_calculation(self):
        """CR-2: Without GST has zero tax and total equals base fee exactly."""
        calc = Enrollment.calculate_gst_breakdown(
            base_fee=Decimal("50000.00"),
            treatment=GSTTreatment.WITHOUT_GST,
            tax_rate=Decimal("18.00"),
        )
        self.assertEqual(calc["tax_rate"], Decimal("0.00"))
        self.assertEqual(calc["taxable_amount"], Decimal("50000.00"))
        self.assertEqual(calc["tax_amount"], Decimal("0.00"))
        self.assertEqual(calc["total_payable"], Decimal("50000.00"))

    def test_enrollment_creation_without_gst(self):
        """CR-2: Enrollment saved with WITHOUT_GST persists zero tax and no GST lines."""
        calc = Enrollment.calculate_gst_breakdown(
            base_fee=Decimal("45000.00"),
            treatment=GSTTreatment.WITHOUT_GST,
        )
        enrollment = Enrollment.objects.create(
            enrollment_number="ENR-NOGST-001",
            lead=self.lead,
            student_name="Ramesh Kumar",
            student_email="ramesh@example.com",
            student_phone="9876501234",
            product=self.product,
            branch=self.branch,
            assigned_counselor=self.counselor,
            base_course_fee=Decimal("45000.00"),
            gst_treatment=GSTTreatment.WITHOUT_GST,
            tax_rate=calc["tax_rate"],
            taxable_amount=calc["taxable_amount"],
            tax_amount=calc["tax_amount"],
            total_payable=calc["total_payable"],
            outstanding_balance=calc["total_payable"],
            payment_plan=PaymentPlan.FULL_PAYMENT,
        )

        self.assertEqual(enrollment.gst_treatment, GSTTreatment.WITHOUT_GST)
        self.assertEqual(enrollment.tax_amount, Decimal("0.00"))
        self.assertEqual(enrollment.total_payable, Decimal("45000.00"))

        txn = PaymentTransaction.objects.create(
            enrollment=enrollment,
            receipt_number="TP-NOGST-1001",
            amount=Decimal("45000.00"),
            payment_method=PaymentMethod.UPI,
            status=PaymentTransactionStatus.APPROVED,
            recorded_by=self.counselor,
        )

        request = self.factory.get("/")
        request.user = self.counselor
        ctx = get_receipt_context(request, txn)

        self.assertTrue(ctx["is_without_gst"])
        self.assertEqual(ctx["document_title"], "Payment Receipt")
        self.assertEqual(ctx["tax_amount"], Decimal("0.00"))
        self.assertEqual(ctx["total_payable"], Decimal("45000.00"))

    def test_legacy_enrollment_unchanged(self):
        """CR-2: Existing historical enrollments retain their amounts."""
        legacy_enr = Enrollment.objects.create(
            enrollment_number="ENR-LEGACY-001",
            lead=self.lead,
            student_name="Legacy Student",
            student_email="legacy@example.com",
            student_phone="9876509999",
            product=self.product,
            branch=self.branch,
            assigned_counselor=self.counselor,
            base_course_fee=Decimal("40000.00"),
            gst_treatment=GSTTreatment.INCLUSIVE,
            tax_rate=Decimal("18.00"),
            taxable_amount=Decimal("33898.31"),
            tax_amount=Decimal("6101.69"),
            total_payable=Decimal("40000.00"),
            outstanding_balance=Decimal("40000.00"),
        )
        self.assertEqual(legacy_enr.gst_treatment, GSTTreatment.INCLUSIVE)
        self.assertEqual(legacy_enr.total_payable, Decimal("40000.00"))
        self.assertEqual(legacy_enr.tax_amount, Decimal("6101.69"))
