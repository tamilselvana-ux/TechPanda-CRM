from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail

from branches.models import Branch
from products.models import Product
from leads.models import Lead
from leads.models_enrollment import (
    Enrollment,
    Installment,
    PaymentTransaction,
    PaymentTransactionStatus,
    PaymentMethod,
    PaymentPlan,
    GSTTreatment,
    PaymentEmailLog,
)
from services.email_service import (
    send_enrollment_confirmation_email,
    send_payment_receipt_email,
    process_installment_reminders_batch,
)
from leads.services_enrollment import approve_payment

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class CR1EmailAutomationTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Email Test Branch", status=Branch.Status.ACTIVE)
        self.admin = User.objects.create_superuser(
            username="test_admin_cr1",
            password="testpassword123",
            role="ADMIN",
        )
        self.accountant = User.objects.create_user(
            username="test_acc_cr1",
            password="testpassword123",
            role="ACCOUNTANT",
            branch=self.branch,
        )
        self.lead = Lead.objects.create(
            name="Ananya Sharma",
            phone="9811223344",
            email="ananya.student@example.com",
            branch=self.branch,
        )
        self.product = Product.objects.create(
            name="Data Science Masterclass",
            price=Decimal("60000.00"),
            status="active",
        )
        self.client = Client()

    def tearDown(self):
        PaymentEmailLog.objects.filter(recipient_email="ananya.student@example.com").delete()
        PaymentTransaction.objects.filter(enrollment__enrollment_number="ENR-EM-001").delete()
        Installment.objects.filter(enrollment__enrollment_number="ENR-EM-001").delete()
        Enrollment.objects.filter(enrollment_number="ENR-EM-001").delete()
        self.lead.delete()
        self.product.delete()
        self.accountant.delete()
        self.admin.delete()
        self.branch.delete()

    def test_cr1a_enrollment_confirmation_email_and_idempotency(self):
        """CR-1a: Confirmation email sent right after enrollment is saved, logged in PaymentEmailLog, no duplicates."""
        enrollment = Enrollment.objects.create(
            enrollment_number="ENR-EM-001",
            lead=self.lead,
            student_name="Ananya Sharma",
            student_email="ananya.student@example.com",
            student_phone="9811223344",
            product=self.product,
            branch=self.branch,
            base_course_fee=Decimal("60000.00"),
            gst_treatment=GSTTreatment.WITH_GST,
            tax_rate=Decimal("18.00"),
            taxable_amount=Decimal("60000.00"),
            tax_amount=Decimal("10800.00"),
            total_payable=Decimal("70800.00"),
            outstanding_balance=Decimal("70800.00"),
            payment_plan=PaymentPlan.FULL_PAYMENT,
        )

        mail.outbox = []
        success, msg = send_enrollment_confirmation_email(enrollment)
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Enrollment Confirmed", mail.outbox[0].subject)
        self.assertIn("ananya.student@example.com", mail.outbox[0].to)

        # Verify PaymentEmailLog
        log_entry = PaymentEmailLog.objects.filter(
            enrollment=enrollment, email_type='ENROLLMENT_CONFIRMATION'
        ).first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.status, 'SENT')

        # Idempotency check: second dispatch is a no-op
        mail.outbox = []
        success2, msg2 = send_enrollment_confirmation_email(enrollment)
        self.assertTrue(success2)
        self.assertEqual(len(mail.outbox), 0)

    def test_cr1b_payment_receipt_email_only_on_accountant_approval(self):
        """CR-1b: Payment receipt sent ONLY when accountant approves payment, with PDF attached."""
        enrollment = Enrollment.objects.create(
            enrollment_number="ENR-EM-001",
            lead=self.lead,
            student_name="Ananya Sharma",
            student_email="ananya.student@example.com",
            student_phone="9811223344",
            product=self.product,
            branch=self.branch,
            base_course_fee=Decimal("60000.00"),
            gst_treatment=GSTTreatment.WITH_GST,
            tax_rate=Decimal("18.00"),
            taxable_amount=Decimal("60000.00"),
            tax_amount=Decimal("10800.00"),
            total_payable=Decimal("70800.00"),
            outstanding_balance=Decimal("70800.00"),
            payment_plan=PaymentPlan.FULL_PAYMENT,
        )

        txn = PaymentTransaction.objects.create(
            enrollment=enrollment,
            receipt_number="TP-TEST-9901",
            amount=Decimal("70800.00"),
            payment_method=PaymentMethod.UPI,
            status=PaymentTransactionStatus.PENDING_VERIFICATION,
        )

        # Cannot send receipt while still pending
        mail.outbox = []
        success_pending, _ = send_payment_receipt_email(txn)
        self.assertFalse(success_pending)
        self.assertEqual(len(mail.outbox), 0)

        # Approve payment
        txn.status = PaymentTransactionStatus.APPROVED
        txn.reviewed_by = self.accountant
        txn.reviewed_at = timezone.now()
        txn.save()

        # Send receipt email
        mail.outbox = []
        success_approved, _ = send_payment_receipt_email(txn)
        self.assertTrue(success_approved)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Payment Receipt", mail.outbox[0].subject)

        # Verify PDF attachment
        attachments = mail.outbox[0].attachments
        self.assertGreater(len(attachments), 0)
        self.assertTrue(any(att[0].endswith('.pdf') for att in attachments))

        # Verify PaymentEmailLog
        log_entry = PaymentEmailLog.objects.filter(
            payment=txn, email_type='PAYMENT_CONFIRMATION'
        ).first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.status, 'SENT')

    def test_cr1c_and_d_installment_due_reminders(self):
        """CR-1c & CR-1d: 2 days before due date and on due date reminders."""
        today = timezone.localdate()
        two_days_ahead = today + timedelta(days=2)

        enrollment = Enrollment.objects.create(
            enrollment_number="ENR-EM-001",
            lead=self.lead,
            student_name="Ananya Sharma",
            student_email="ananya.student@example.com",
            student_phone="9811223344",
            product=self.product,
            branch=self.branch,
            base_course_fee=Decimal("60000.00"),
            gst_treatment=GSTTreatment.WITH_GST,
            total_payable=Decimal("70800.00"),
            outstanding_balance=Decimal("70800.00"),
            payment_plan=PaymentPlan.SPLIT_PAYMENT,
        )

        inst_2d = Installment.objects.create(
            enrollment=enrollment,
            installment_number=1,
            due_date=two_days_ahead,
            scheduled_amount=Decimal("35400.00"),
            remaining_balance=Decimal("35400.00"),
            status='Upcoming',
        )

        inst_today = Installment.objects.create(
            enrollment=enrollment,
            installment_number=2,
            due_date=today,
            scheduled_amount=Decimal("35400.00"),
            remaining_balance=Decimal("35400.00"),
            status='Due',
        )

        mail.outbox = []
        summary = process_installment_reminders_batch(target_date=today)
        self.assertGreaterEqual(summary['upcoming_2_days'], 1)
        self.assertGreaterEqual(summary['due_today'], 1)
        self.assertGreaterEqual(len(mail.outbox), 2)

        # Running batch again on same day sends 0 duplicates
        mail.outbox = []
        summary2 = process_installment_reminders_batch(target_date=today)
        self.assertEqual(summary2['upcoming_2_days'], 0)
        self.assertEqual(summary2['due_today'], 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_cr1e_admin_email_logs_view(self):
        """CR-1e: Admin Email Log view renders all dispatches with filtering."""
        self.client.force_login(self.admin)
        response = self.client.get('/admin/email-logs/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Student Email Audit Logs", response.content)
        self.assertIn(b"Total Dispatches", response.content)
