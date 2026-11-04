from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from branches.models import Branch
from products.models import Product
from leads.models import Lead
from leads.models_enrollment import Enrollment, GSTTreatment, PaymentPlan

User = get_user_model()


class ProductDeleteTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Product Test Branch", status=Branch.Status.ACTIVE)
        self.admin = User.objects.create_superuser(
            username="admin_cr8_test",
            password="testpassword123",
            role="ADMIN",
        )
        self.client = Client()
        self.client.force_login(self.admin)

    def tearDown(self):
        Enrollment.objects.filter(student_email="prod_test@example.com").delete()
        Lead.objects.filter(email="prod_test@example.com").delete()
        Product.objects.filter(name__startswith="CR8 Product").delete()
        self.admin.delete()
        self.branch.delete()

    def test_delete_blocked_when_leads_exist(self):
        """CR-8: Block product deletion when leads are attached."""
        prod = Product.objects.create(
            name="CR8 Product With Leads",
            price=Decimal("45000.00"),
            status="Active"
        )
        Lead.objects.create(
            name="Lead Attached",
            phone="9871112223",
            email="prod_test@example.com",
            branch=self.branch,
            product=prod,
        )

        response = self.client.post(f'/admin/products/{prod.pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(pk=prod.pk).exists())

    def test_delete_blocked_when_enrollments_exist(self):
        """CR-8: Block product deletion when student enrollments are attached."""
        prod = Product.objects.create(
            name="CR8 Product With Enrollments",
            price=Decimal("45000.00"),
            status="Active"
        )
        lead = Lead.objects.create(
            name="Student Attached",
            phone="9871112224",
            email="prod_test@example.com",
            branch=self.branch,
        )
        Enrollment.objects.create(
            enrollment_number="ENR-CR8-001",
            lead=lead,
            student_name="Student Attached",
            student_email="prod_test@example.com",
            student_phone="9871112224",
            product=prod,
            branch=self.branch,
            base_course_fee=Decimal("45000.00"),
            gst_treatment=GSTTreatment.WITHOUT_GST,
            total_payable=Decimal("45000.00"),
            outstanding_balance=Decimal("45000.00"),
            payment_plan=PaymentPlan.FULL_PAYMENT,
        )

        response = self.client.post(f'/admin/products/{prod.pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(pk=prod.pk).exists())

    def test_delete_allowed_when_zero_leads_and_enrollments(self):
        """CR-8: Allow product deletion when unused."""
        prod = Product.objects.create(
            name="CR8 Product Unused",
            price=Decimal("30000.00"),
            status="Active"
        )

        response = self.client.post(f'/admin/products/{prod.pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=prod.pk).exists())
