from django.test import TestCase, Client
from django.urls import reverse
import time

from django.utils import timezone
from accounts.models import User, UserRole
from branches.models import Branch
from leads.models import Lead
from calls.models import CallHistory
from followups.models import FollowUp


class TelecallersPerformanceAndLoginTests(TestCase):
    """
    Automated verification of:
    - /accounts/login/ alias route returning HTTP 200
    - /admin/telecallers/ loading cleanly without ASGI / Daphne timeouts
    - Subquery annotation accuracy for lead_count, call_count, followup_count
    """

    def setUp(self):
        self.client = Client()
        self.branch = Branch.objects.create(name="Performance Hub", status="Active")
        self.admin = User.objects.create_superuser(
            username="admin_perf_tester",
            email="admin_perf@techpanda.test",
            password="AdminPassword123!"
        )
        self.telecaller = User.objects.create_user(
            username="tc_perf_user",
            email="tc_perf@techpanda.test",
            role=UserRole.TELECALLER,
            branch=self.branch,
            password="TelecallerPassword123!"
        )

        # Seed test data for counts
        for i in range(5):
            lead = Lead.objects.create(
                name=f"Lead {i}",
                phone=f"900000000{i}",
                assigned_telecaller=self.telecaller,
                branch=self.branch
            )
            CallHistory.objects.create(
                lead=lead,
                telecaller=self.telecaller
            )
            FollowUp.objects.create(
                lead=lead,
                telecaller=self.telecaller,
                follow_up_date=timezone.now().date()
            )

    def test_01_accounts_login_alias_returns_200(self):
        """GET /accounts/login/ returns HTTP 200 instead of 404."""
        resp = self.client.get('/accounts/login/')
        self.assertEqual(resp.status_code, 200)

    def test_02_admin_telecallers_list_performance_and_counts(self):
        """GET /admin/telecallers/ returns HTTP 200 fast with accurate subquery counts."""
        self.client.login(username="admin_perf_tester", password="AdminPassword123!")
        t0 = time.time()
        resp = self.client.get(reverse('admin_telecallers_list'))
        t1 = time.time()
        self.assertEqual(resp.status_code, 200)
        self.assertLess(t1 - t0, 3.0, "admin_telecallers_list took longer than 3 seconds")

        page_obj = resp.context['page_obj']
        tc_item = next((u for u in page_obj if u.pk == self.telecaller.pk), None)
        self.assertIsNotNone(tc_item)
        self.assertEqual(tc_item.lead_count, 5)
        self.assertEqual(tc_item.call_count, 5)
        self.assertEqual(tc_item.followup_count, 5)
