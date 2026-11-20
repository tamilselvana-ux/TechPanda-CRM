from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from accounts.models import User, UserRole
from branches.models import Branch


class UserCreateNavigationAndFormTests(TestCase):
    """
    Automated verification of User Creation entrypoints, query-param pre-population,
    action button existence across all role lists, and successful user creation.
    """

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username="admin_nav_tester",
            email="admin_nav@techpanda.test",
            phone="9876543210",
            password="AdminPassword123!"
        )
        self.client.login(username="admin_nav_tester", password="AdminPassword123!")

        self.branch = Branch.objects.create(name="T. Nagar Tech Hub", status="Active")

    def test_01_user_create_get_without_params(self):
        """GET /admin/users/create/ renders 200 with blank role."""
        url = reverse('admin_user_create')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)
        form = resp.context['form']
        self.assertIsNone(form.initial.get('role'))

    def test_02_user_create_prepopulates_role_from_query(self):
        """GET /admin/users/create/?role=COUNSELOR pre-populates role initial data."""
        url = reverse('admin_user_create') + f"?role={UserRole.COUNSELOR}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        self.assertEqual(form.initial.get('role'), UserRole.COUNSELOR)

    def test_03_user_create_prepopulates_branch_from_query(self):
        """GET /admin/users/create/?branch=<id> pre-populates branch initial data."""
        url = reverse('admin_user_create') + f"?branch={self.branch.pk}"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        self.assertEqual(form.initial.get('branch'), self.branch.pk)

    def test_04_users_list_contains_add_new_user_button(self):
        """All Staff page (/admin/users/) renders Add New User button."""
        resp = self.client.get(reverse('admin_users_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse('admin_user_create'))
        self.assertContains(resp, "Add New User")

    def test_05_counselors_list_contains_add_counselor_button(self):
        """Counselors page renders Add Counselor button with role param."""
        resp = self.client.get(reverse('admin_counselors_list'))
        self.assertEqual(resp.status_code, 200)
        expected_target = f"{reverse('admin_user_create')}?role={UserRole.COUNSELOR}"
        self.assertContains(resp, expected_target)
        self.assertContains(resp, "Add Counselor")

    def test_06_branch_admins_list_contains_add_branch_admin_button(self):
        """Branch Admins page renders Add Branch Admin button with role param."""
        resp = self.client.get(reverse('admin_branch_admins_list'))
        self.assertEqual(resp.status_code, 200)
        expected_target = f"{reverse('admin_user_create')}?role={UserRole.BRANCH_ADMIN}"
        self.assertContains(resp, expected_target)
        self.assertContains(resp, "Add Branch Admin")

    def test_07_receptionists_list_contains_add_receptionist_button(self):
        """Receptionists page renders Add Receptionist button with role param."""
        resp = self.client.get(reverse('admin_receptionists_list'))
        self.assertEqual(resp.status_code, 200)
        expected_target = f"{reverse('admin_user_create')}?role={UserRole.RECEPTIONIST}"
        self.assertContains(resp, expected_target)
        self.assertContains(resp, "Add Receptionist")

    def test_08_sales_heads_list_contains_add_sales_head_button(self):
        """Sales Heads page renders Add Sales Head button with role param."""
        resp = self.client.get(reverse('admin_managers_list'))
        self.assertEqual(resp.status_code, 200)
        expected_target = f"{reverse('admin_user_create')}?role={UserRole.SALES_HEAD}"
        self.assertContains(resp, expected_target)
        self.assertContains(resp, "Add Sales Head")

    def test_09_branch_heads_list_contains_add_branch_head_button(self):
        """Branch Heads page renders Add Branch Head button with role param."""
        resp = self.client.get(reverse('admin_branch_heads_list'))
        self.assertEqual(resp.status_code, 200)
        expected_target = f"{reverse('admin_user_create')}?role={UserRole.BRANCH_HEAD}"
        self.assertContains(resp, expected_target)
        self.assertContains(resp, "Add Branch Head")

    def test_10_accountants_list_contains_add_accountant_button(self):
        """Accountants page renders Add Accountant button with role param."""
        resp = self.client.get(reverse('admin_accountants_list'))
        self.assertEqual(resp.status_code, 200)
        expected_target = f"{reverse('admin_user_create')}?role={UserRole.ACCOUNTANT}"
        self.assertContains(resp, expected_target)
        self.assertContains(resp, "Add Accountant")

    def test_11_marketing_list_contains_add_marketing_button(self):
        """Marketing Team page renders Add Marketing Staff button."""
        resp = self.client.get(reverse('admin_marketing_users_list'))
        self.assertEqual(resp.status_code, 200)
        expected_target = f"{reverse('admin_user_create')}?role={UserRole.MARKETING}"
        self.assertContains(resp, expected_target)

    def test_12_sidebar_contains_add_team_member_link(self):
        """Sidebar contains Add Team Member link in Team & Staff section."""
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Add Team Member")
        self.assertContains(resp, reverse('admin_user_create'))

    @patch('accounts.views.send_user_welcome_email')
    def test_13_create_user_post_success_and_redirect(self, mock_welcome_email):
        """Submitting valid staff user data creates user, provisions pending invitation, and redirects to role list."""
        mock_welcome_email.return_value = (True, "Welcome email sent successfully.")

        payload = {
            'first_name': 'Kavitha',
            'last_name': 'Raman',
            'email': 'kavitha.counselor@techpanda.test',
            'phone': '9840998877',
            'role': UserRole.COUNSELOR,
            'branch': self.branch.pk,
        }

        resp = self.client.post(reverse('admin_user_create'), data=payload)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('admin_counselors_list'))

        user = User.objects.filter(email='kavitha.counselor@techpanda.test').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'Kavitha')
        self.assertEqual(user.last_name, 'Raman')
        self.assertEqual(user.role, UserRole.COUNSELOR)
        self.assertEqual(user.branch, self.branch)
        # Pending invitation status until user opens secure email link to activate
        self.assertFalse(user.is_active)
        self.assertEqual(user.invitation_status, 'PENDING')
        self.assertTrue(user.must_change_password)
        self.assertTrue(len(user.username) > 0)
        mock_welcome_email.assert_called_once()
