from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, UserRole
from branches.models import Branch


class StaffCountsAndFiltersTestCase(TestCase):
    def setUp(self):
        self.branch_a = Branch.objects.create(name="North Center", status="Active")
        self.branch_b = Branch.objects.create(name="South Center", status="Active")

        # Admin user
        self.admin_user = User.objects.create_superuser(
            username="admin_test",
            email="admin@techpanda.test",
            password="testpassword123",
            role=UserRole.SUPERADMIN,
            is_active=True
        )

        # Sales Heads
        self.sh1 = User.objects.create_user(
            username="sh1", email="sh1@test.com", password="pass", role=UserRole.SALES_HEAD, is_active=True
        )
        self.sh2 = User.objects.create_user(
            username="sh2", email="sh2@test.com", password="pass", role=UserRole.SALES_HEAD, is_active=False
        )

        # Branch Heads
        self.bh1 = User.objects.create_user(
            username="bh1", email="bh1@test.com", password="pass", role=UserRole.BRANCH_HEAD, branch=self.branch_a, is_active=True
        )

        # Branch Admins
        self.ba1 = User.objects.create_user(
            username="ba1", email="ba1@test.com", password="pass", role=UserRole.BRANCH_ADMIN, branch=self.branch_a, is_active=True
        )
        self.ba2 = User.objects.create_user(
            username="ba2", email="ba2@test.com", password="pass", role=UserRole.BRANCH_ADMIN, branch=self.branch_b, is_active=False
        )

        # Counselors
        self.c1 = User.objects.create_user(
            username="c1", email="c1@test.com", password="pass", role=UserRole.COUNSELOR, branch=self.branch_a, is_active=True
        )

        # Telecallers
        self.tc1 = User.objects.create_user(
            username="tc1", email="tc1@test.com", password="pass", role=UserRole.TELECALLER, branch=self.branch_a, is_active=True
        )
        self.tc2 = User.objects.create_user(
            username="tc2", email="tc2@test.com", password="pass", role=UserRole.TELECALLER, branch=self.branch_b, is_active=False
        )

        # Receptionists
        self.rec1 = User.objects.create_user(
            username="rec1", email="rec1@test.com", password="pass", role=UserRole.RECEPTIONIST, branch=self.branch_a, is_active=True
        )

        # Accountants
        self.acc1 = User.objects.create_user(
            username="acc1", email="acc1@test.com", password="pass", role=UserRole.ACCOUNTANT, branch=self.branch_b, is_active=True
        )

        self.client = Client()
        self.client.force_login(self.admin_user)

    def test_sidebar_context_processor_staff_counts(self):
        response = self.client.get(reverse('admin_users_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('staff_counts', response.context)
        sc = response.context['staff_counts']
        self.assertEqual(sc['sales_heads'], 2)
        self.assertEqual(sc['branch_heads'], 1)
        self.assertEqual(sc['branch_admins'], 2)
        self.assertEqual(sc['counselors'], 1)
        self.assertEqual(sc['telecallers'], 2)
        self.assertEqual(sc['receptionists'], 1)
        self.assertEqual(sc['accountants'], 1)
        self.assertGreaterEqual(sc['total'], 10)

    def test_admin_users_list_role_filtering_case_insensitive(self):
        # Filtering with uppercase
        resp_upper = self.client.get(reverse('admin_users_list') + '?role=COUNSELOR')
        self.assertEqual(resp_upper.status_code, 200)
        self.assertEqual(resp_upper.context['total_count'], 1)

        # Filtering with lowercase
        resp_lower = self.client.get(reverse('admin_users_list') + '?role=counselor')
        self.assertEqual(resp_lower.status_code, 200)
        self.assertEqual(resp_lower.context['total_count'], 1)

    def test_admin_users_list_scoped_active_inactive_counts(self):
        # Filter by branch_b where ba2 and tc2 are inactive, acc1 is active
        url = reverse('admin_users_list') + f'?branch={self.branch_b.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        total = response.context['total_count']
        active = response.context['active_count']
        inactive = response.context['inactive_count']
        self.assertEqual(total, 3)
        self.assertEqual(active, 1)
        self.assertEqual(inactive, 2)
        self.assertEqual(active + inactive, total)

    def test_role_specific_list_views_kpi_counts(self):
        # Sales Heads
        resp_sh = self.client.get(reverse('admin_managers_list'))
        self.assertEqual(resp_sh.status_code, 200)
        self.assertEqual(resp_sh.context['total_count'], 2)
        self.assertEqual(resp_sh.context['active_count'], 1)
        self.assertEqual(resp_sh.context['inactive_count'], 1)
        self.assertContains(resp_sh, "2 Sales Heads")

        # Branch Heads
        resp_bh = self.client.get(reverse('admin_branch_heads_list'))
        self.assertEqual(resp_bh.status_code, 200)
        self.assertEqual(resp_bh.context['total_count'], 1)
        self.assertEqual(resp_bh.context['active_count'], 1)
        self.assertEqual(resp_bh.context['inactive_count'], 0)
        self.assertContains(resp_bh, "1 Branch Head")

        # Branch Admins
        resp_ba = self.client.get(reverse('admin_branch_admins_list') + f'?branch={self.branch_b.id}')
        self.assertEqual(resp_ba.status_code, 200)
        self.assertEqual(resp_ba.context['total_count'], 1)
        self.assertEqual(resp_ba.context['active_count'], 0)
        self.assertEqual(resp_ba.context['inactive_count'], 1)

        # Counselors
        resp_c = self.client.get(reverse('admin_counselors_list'))
        self.assertEqual(resp_c.status_code, 200)
        self.assertEqual(resp_c.context['total_count'], 1)
        self.assertEqual(resp_c.context['active_count'], 1)
        self.assertEqual(resp_c.context['inactive_count'], 0)
        self.assertContains(resp_c, "1 Counselor")

        # Telecallers
        resp_tc = self.client.get(reverse('admin_telecallers_list'))
        self.assertEqual(resp_tc.status_code, 200)
        self.assertEqual(resp_tc.context['total_count'], 2)
        self.assertEqual(resp_tc.context['active_count'], 1)
        self.assertEqual(resp_tc.context['inactive_count'], 1)
        self.assertContains(resp_tc, "2 Telecallers")

        # Receptionists
        resp_rec = self.client.get(reverse('admin_receptionists_list') + f'?branch={self.branch_a.id}')
        self.assertEqual(resp_rec.status_code, 200)
        self.assertEqual(resp_rec.context['total_receptionists'], 1)
        self.assertEqual(resp_rec.context['active_count'], 1)
        self.assertEqual(resp_rec.context['inactive_count'], 0)

        # Accountants
        resp_acc = self.client.get(reverse('admin_accountants_list') + f'?branch={self.branch_b.id}')
        self.assertEqual(resp_acc.status_code, 200)
        self.assertEqual(resp_acc.context['total_accountants'], 1)
        self.assertEqual(resp_acc.context['active_accountants'], 1)
        self.assertEqual(resp_acc.context['inactive_accountants'], 0)

    def test_dashboard_headcount_strip_includes_all_staff_roles(self):
        resp_dash = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp_dash.status_code, 200)
        self.assertIn('total_staff', resp_dash.context)
        self.assertIn('total_branch_admins', resp_dash.context)
        self.assertIn('total_receptionists', resp_dash.context)
        self.assertIn('total_accountants', resp_dash.context)
        self.assertGreaterEqual(resp_dash.context['total_staff'], 10)

    def test_telecallers_table_serial_number_and_counts(self):
        response = self.client.get(reverse('admin_telecallers_list'))
        self.assertEqual(response.status_code, 200)
        # ID column must be replaced by #
        self.assertContains(response, ">#<")
        self.assertNotContains(response, '<th style="width: 50px;">ID</th>')
        # Row counts must be visible
        self.assertContains(response, "Showing")
        self.assertContains(response, "Telecallers")
        # Role switcher tabs bar must be rendered
        self.assertContains(response, "All Staff")
        self.assertContains(response, "Counselors")
        self.assertContains(response, "Sales Heads")
        self.assertContains(response, "Branch Heads")
        self.assertContains(response, "Branch Admins")
        self.assertContains(response, "Receptionists")
        self.assertContains(response, "Accountants")

    def test_telecallers_page_size_handling(self):
        # Test with custom page_size
        resp_size = self.client.get(reverse('admin_telecallers_list') + '?page_size=25')
        self.assertEqual(resp_size.status_code, 200)
        self.assertEqual(resp_size.context['page_size'], '25')

        # Test with page_size=all
        resp_all = self.client.get(reverse('admin_telecallers_list') + '?page_size=all')
        self.assertEqual(resp_all.status_code, 200)
        self.assertEqual(resp_all.context['page_size'], 'all')

    def test_users_list_serial_number_and_role_tabs(self):
        response = self.client.get(reverse('admin_users_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ">#<")
        self.assertContains(response, "All Staff")

