from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from branches.models import Branch

User = get_user_model()


class AccountantDashboardDateRangeTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Accountant Date Branch", status=Branch.Status.ACTIVE)
        self.accountant = User.objects.create_user(
            username="acc_cr4_test",
            password="testpassword123",
            role="ACCOUNTANT",
            branch=self.branch,
        )
        self.client = Client()
        self.client.force_login(self.accountant)

    def tearDown(self):
        self.accountant.delete()
        self.branch.delete()

    def test_default_date_range_is_current_month(self):
        """CR-4: When no date params are provided, default to current month."""
        response = self.client.get('/accountant/dashboard/')
        self.assertEqual(response.status_code, 200)
        today = timezone.localdate()
        expected_start = today.replace(day=1).strftime('%Y-%m-%d')
        self.assertEqual(response.context['start_date'], expected_start)

    def test_custom_date_range_filters_and_persists(self):
        """CR-4: Custom date range is applied and returned in context."""
        response = self.client.get('/accountant/dashboard/?start_date=2026-10-05&end_date=2026-10-20')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['start_date'], '2026-10-05')
        self.assertEqual(response.context['end_date'], '2026-10-20')

    def test_edge_case_start_after_end_does_not_crash(self):
        """CR-4: When start_date > end_date, do not crash; default to current month."""
        response = self.client.get('/accountant/dashboard/?start_date=2026-10-25&end_date=2026-10-05')
        self.assertEqual(response.status_code, 200)
        today = timezone.localdate()
        expected_start = today.replace(day=1).strftime('%Y-%m-%d')
        self.assertEqual(response.context['start_date'], expected_start)

    def test_edge_case_empty_data_range_returns_clean_zero_state(self):
        """CR-4: Period with no transactions returns 0 totals without 500 error."""
        response = self.client.get('/accountant/dashboard/?start_date=2020-01-01&end_date=2020-01-10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_collection'], Decimal('0.00'))
        self.assertEqual(response.context['cash_received'], Decimal('0.00'))
        self.assertEqual(response.context['account_received'], Decimal('0.00'))
