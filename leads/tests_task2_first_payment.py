import os
import sys
from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone
from accounts.models import User, UserRole
from branches.models import Branch
from products.models import Product
from leads.models import Lead
from leads.models_enrollment import Enrollment, PaymentPlan, PaymentTransaction, PaymentTransactionStatus

class Task2FirstPaymentTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Task2 Branch", status="Active")
        self.counselor = User.objects.create_user(
            username="task2_counselor",
            email="counselor_t2@example.com",
            password="Password123!",
            role=UserRole.COUNSELOR,
            branch=self.branch
        )
        self.admin = User.objects.create_user(
            username="task2_admin",
            email="admin_t2@example.com",
            password="Password123!",
            role=UserRole.ADMIN
        )
        self.product = Product.objects.create(
            name="Task2 Course",
            price=Decimal("40000.00"),
            status=Product.Status.ACTIVE
        )
        self.lead = Lead.objects.create(
            name="Student One",
            phone="9988776655",
            email="student1@example.com",
            branch=self.branch,
            product=self.product,
            assigned_counselor=self.counselor
        )

    def test_enrollment_without_first_payment(self):
        client = Client()
        client.force_login(self.counselor)
        post_data = {
            'student_name': 'Student One',
            'student_phone': '9988776655',
            'student_email': 'student1@example.com',
            'product_id': self.product.id,
            'branch_id': self.branch.id,
            'base_course_fee': '40000.00',
            'gst_treatment': 'WITH_GST',
            'tax_rate': '18',
            'payment_plan': PaymentPlan.FULL_PAYMENT,
            'first_payment_amount': '', # No payment
        }
        res = client.post(f'/leads/{self.lead.id}/enroll/', post_data)
        self.assertEqual(res.status_code, 302)
        enrollment = Enrollment.objects.filter(lead=self.lead).first()
        self.assertIsNotNone(enrollment)
        self.assertEqual(enrollment.payments.count(), 0)

    def test_enrollment_with_first_payment_queued_for_accountant(self):
        lead2 = Lead.objects.create(
            name="Student Two",
            phone="9988776656",
            email="student2@example.com",
            branch=self.branch,
            product=self.product,
            assigned_counselor=self.counselor
        )
        client = Client()
        client.force_login(self.counselor)
        post_data = {
            'student_name': 'Student Two',
            'student_phone': '9988776656',
            'student_email': 'student2@example.com',
            'product_id': self.product.id,
            'branch_id': self.branch.id,
            'base_course_fee': '40000.00',
            'gst_treatment': 'WITHOUT_GST',
            'payment_plan': PaymentPlan.FULL_PAYMENT,
            'first_payment_amount': '10000.00',
            'first_payment_method': 'UPI',
            'first_payment_reference': 'UPI-REF-998822',
            'first_payment_notes': 'Initial token payment',
        }
        res = client.post(f'/leads/{lead2.id}/enroll/', post_data)
        self.assertEqual(res.status_code, 302)
        enrollment = Enrollment.objects.filter(lead=lead2).first()
        self.assertIsNotNone(enrollment)
        self.assertEqual(enrollment.payments.count(), 1)
        payment = enrollment.payments.first()
        self.assertEqual(payment.amount, Decimal('10000.00'))
        self.assertEqual(payment.payment_method, 'UPI')
        self.assertEqual(payment.transaction_reference, 'UPI-REF-998822')
        self.assertEqual(payment.status, PaymentTransactionStatus.PENDING_VERIFICATION)
        self.assertEqual(payment.recorded_by, self.counselor)

    def test_first_payment_excess_amount_rolls_back(self):
        lead3 = Lead.objects.create(
            name="Student Three",
            phone="9988776657",
            email="student3@example.com",
            branch=self.branch,
            product=self.product,
            assigned_counselor=self.counselor
        )
        client = Client()
        client.force_login(self.counselor)
        post_data = {
            'student_name': 'Student Three',
            'student_phone': '9988776657',
            'student_email': 'student3@example.com',
            'product_id': self.product.id,
            'branch_id': self.branch.id,
            'base_course_fee': '40000.00',
            'gst_treatment': 'WITHOUT_GST',
            'payment_plan': PaymentPlan.FULL_PAYMENT,
            'first_payment_amount': '50000.00', # Exceeds 40,000!
            'first_payment_method': 'Cash',
        }
        res = client.post(f'/leads/{lead3.id}/enroll/', post_data)
        self.assertEqual(res.status_code, 200) # Re-rendered with error message
        enrollment = Enrollment.objects.filter(lead=lead3).first()
        self.assertIsNone(enrollment, "Enrollment must be rolled back on first payment error")
