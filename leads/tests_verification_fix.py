import os
import sys
from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone

from accounts.models import User
from branches.models import Branch
from products.models import Product
from leads.models import Lead, LeadCategory
from leads.models_enrollment import (
    Enrollment,
    Installment,
    PaymentTransaction,
    PaymentTransactionStatus,
    PaymentMethod,
    GSTTreatment,
    PaymentPlan
)


class AccountantVerificationQueueTests(TestCase):
    """
    CR-5 Regression Test Suite:
    Validates /accountant/verification/?status=PENDING_VERIFICATION renders records
    with full student, course, installment, GST breakdown, mode, ref, proof, and actions.
    """

    def setUp(self):
        self.client = Client()

        # Create branch
        self.branch = Branch.objects.create(name='Test HQ Branch', status='Active')

        # Create accountant user
        self.accountant = User.objects.create(
            username='test_acc_cr5',
            email='acc_cr5@test.com',
            role='ACCOUNTANT',
            is_active=True,
            branch=self.branch
        )
        self.accountant.set_password('pass123')
        self.accountant.save()

        # Create counselor
        self.counselor = User.objects.create(
            username='counselor_cr5',
            email='counselor_cr5@test.com',
            role='COUNSELOR',
            is_active=True,
            branch=self.branch
        )

        # Create product
        self.product = Product.objects.create(
            name='Full Stack AI Engineering',
            status='Active'
        )

        # Create lead
        self.lead = Lead.objects.create(
            name='John Doe',
            phone='9876543210',
            email='john@example.com',
            branch=self.branch,
            category=LeadCategory.TRAINING,
            source='Walk-in',
            status='New'
        )

        # Create enrollment with 18% GST
        self.enrollment = Enrollment.objects.create(
            lead=self.lead,
            enrollment_number='ENR-CR5-TEST-001',
            student_name='John Doe',
            student_email='john@example.com',
            student_phone='9876543210',
            branch=self.branch,
            product=self.product,
            assigned_counselor=self.counselor,
            base_course_fee=Decimal('50000.00'),
            gst_treatment=GSTTreatment.INCLUSIVE,
            tax_rate=Decimal('18.00'),
            taxable_amount=Decimal('42372.88'),
            tax_amount=Decimal('7627.12'),
            total_payable=Decimal('50000.00'),
            payment_plan=PaymentPlan.SPLIT_PAYMENT,
            status='Active'
        )

        self.installment = Installment.objects.create(
            enrollment=self.enrollment,
            installment_number=1,
            scheduled_amount=Decimal('25000.00'),
            remaining_balance=Decimal('25000.00'),
            due_date=timezone.localdate(),
            status='Upcoming'
        )

        # Create a pending payment
        self.pending_payment = PaymentTransaction.objects.create(
            enrollment=self.enrollment,
            installment=self.installment,
            amount=Decimal('25000.00'),
            payment_method=PaymentMethod.UPI,
            transaction_reference='UPI999888777',
            receipt_number='REC-CR5-PENDING-001',
            status=PaymentTransactionStatus.PENDING_VERIFICATION,
            recorded_by=self.counselor,
            payment_date=timezone.now()
        )

    def test_pending_verification_query_param_renders_records(self):
        """TEST-CR5-01: /accountant/verification/?status=PENDING_VERIFICATION must list pending records."""
        self.client.force_login(self.accountant)

        response = self.client.get('/accountant/verification/?status=PENDING_VERIFICATION')
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Verify record exists in response
        self.assertIn('REC-CR5-PENDING-001', content)
        self.assertIn('John Doe', content)
        self.assertIn('Full Stack AI Engineering', content)
        self.assertIn('UPI999888777', content)
        self.assertIn('Inst #1', content)

        # Verify GST Breakup is rendered
        self.assertIn('Base:', content)
        self.assertIn('GST', content)

        # Verify action buttons exist
        self.assertIn('Approve', content)
        self.assertIn('Reject', content)

    def test_default_status_loads_pending_verification(self):
        """Visiting /accountant/verification/ without status param defaults to pending queue."""
        self.client.force_login(self.accountant)

        response = self.client.get('/accountant/verification/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('REC-CR5-PENDING-001', content)

    def test_approved_tab_filtering(self):
        """Status APPROVED query param correctly filters approved records."""
        # Approve the payment
        self.pending_payment.status = PaymentTransactionStatus.APPROVED
        self.pending_payment.reviewed_by = self.accountant
        self.pending_payment.save()

        self.client.force_login(self.accountant)
        response = self.client.get('/accountant/verification/?status=APPROVED')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('REC-CR5-PENDING-001', content)
        self.assertIn('Approved', content)

    def test_empty_state_message_when_truly_empty(self):
        """When no pending payments exist, shows 'No payments waiting for verification'."""
        PaymentTransaction.objects.all().delete()

        self.client.force_login(self.accountant)
        response = self.client.get('/accountant/verification/?status=PENDING_VERIFICATION')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('No payments waiting for verification.', content)
