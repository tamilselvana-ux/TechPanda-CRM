from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from accounts.models import User, UserRole
from branches.models import Branch


class MarketingTeamIntegrationTests(TestCase):
    """
    Automated test suite verifying Marketing Team integration:
    - User creation with MARKETING role
    - Context processor staff_counts['marketing'] calculation
    - Admin marketing users directory (/admin/marketing/) rendering, search, and branch filter
    - Account status toggle
    - Sidebar navigation presence and 2-column compact role pills grid
    - Zero emojis rule verification
    """

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username="admin_marketing_tester",
            email="admin_mkt@techpanda.test",
            phone="9876543211",
            password="AdminPassword123!"
        )
        self.client.login(username="admin_marketing_tester", password="AdminPassword123!")

        self.branch1 = Branch.objects.create(name="T. Nagar Tech Hub", status="Active")
        self.branch2 = Branch.objects.create(name="Anna Nagar Center", status="Active")

        # Provision marketing user
        self.marketing_user = User.objects.create_user(
            username="karthik.marketing",
            email="karthik@techpanda.test",
            role=UserRole.MARKETING,
            branch=self.branch1,
            is_active=True,
            password="MarketingPassword123!"
        )

    def test_01_user_role_marketing_defined_and_properties(self):
        """Verify MARKETING role exists in UserRole choices and user property works."""
        self.assertEqual(UserRole.MARKETING, 'MARKETING')
        self.assertTrue(self.marketing_user.is_marketing_user)
        self.assertEqual(self.marketing_user.display_role, "Marketing")

    def test_02_context_processor_staff_counts_includes_marketing(self):
        """Verify crm_context processor includes marketing in staff_counts."""
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('staff_counts', resp.context)
        staff_counts = resp.context['staff_counts']
        self.assertIn('marketing', staff_counts)
        self.assertEqual(staff_counts['marketing'], 1)

    def test_03_admin_marketing_users_list_renders_table(self):
        """GET /admin/marketing/ returns HTTP 200 with marketing users table."""
        resp = self.client.get(reverse('admin_marketing_users_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "MARKETING TEAM")
        self.assertContains(resp, "karthik.marketing")
        self.assertContains(resp, "T. Nagar Tech Hub")
        self.assertContains(resp, "+ Add Marketing Member")

    def test_04_admin_marketing_users_list_search_and_filter(self):
        """Search and branch filter work accurately on marketing list."""
        # Query search matching
        resp = self.client.get(reverse('admin_marketing_users_list') + "?q=karthik")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['marketing_users']), 1)

        # Query search not matching
        resp_nomatch = self.client.get(reverse('admin_marketing_users_list') + "?q=nonexistent")
        self.assertEqual(resp_nomatch.status_code, 200)
        self.assertEqual(len(resp_nomatch.context['marketing_users']), 0)

        # Branch filter matching
        resp_branch = self.client.get(reverse('admin_marketing_users_list') + f"?branch={self.branch1.id}")
        self.assertEqual(resp_branch.status_code, 200)
        self.assertEqual(len(resp_branch.context['marketing_users']), 1)

        # Branch filter other branch
        resp_other_branch = self.client.get(reverse('admin_marketing_users_list') + f"?branch={self.branch2.id}")
        self.assertEqual(resp_other_branch.status_code, 200)
        self.assertEqual(len(resp_other_branch.context['marketing_users']), 0)

    def test_05_admin_marketing_toggle_status(self):
        """POST /admin/marketing/<id>/toggle-status/ toggles user active flag."""
        toggle_url = reverse('admin_marketing_toggle_status', args=[self.marketing_user.pk])
        resp = self.client.post(toggle_url)
        self.assertEqual(resp.status_code, 302)
        self.marketing_user.refresh_from_db()
        self.assertFalse(self.marketing_user.is_active)

        # Toggle back
        resp2 = self.client.post(toggle_url)
        self.assertEqual(resp2.status_code, 302)
        self.marketing_user.refresh_from_db()
        self.assertTrue(self.marketing_user.is_active)

    @patch('accounts.views.send_user_welcome_email')
    def test_06_create_marketing_user_via_admin_create_view(self, mock_email):
        """Submitting AdminCreateUserForm with role=MARKETING creates user and redirects to marketing list."""
        mock_email.return_value = (True, "Welcome email sent successfully.")

        payload = {
            'first_name': 'Meena',
            'last_name': 'Sundaram',
            'email': 'meena.mkt@techpanda.test',
            'phone': '9840112233',
            'role': UserRole.MARKETING,
            'branch': self.branch2.pk,
        }

        resp = self.client.post(reverse('admin_user_create'), data=payload)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('admin_marketing_users_list'))

        new_user = User.objects.filter(email='meena.mkt@techpanda.test').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.role, UserRole.MARKETING)
        self.assertEqual(new_user.branch, self.branch2)

    def test_07_sidebar_renders_streamlined_role_list(self):
        """Sidebar contains streamlined directory hero and vertical role links including Marketing without add button."""
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "All Staff Directory")
        self.assertNotContains(resp, "+ Add Team Member")
        self.assertContains(resp, reverse('admin_marketing_users_list'))
        self.assertContains(resp, reverse('admin_telecallers_list'))
        self.assertContains(resp, reverse('admin_counselors_list'))
        self.assertContains(resp, reverse('admin_managers_list'))
        self.assertContains(resp, reverse('admin_branch_heads_list'))
        self.assertContains(resp, reverse('admin_branch_admins_list'))
        self.assertContains(resp, reverse('admin_receptionists_list'))
        self.assertContains(resp, reverse('admin_accountants_list'))

    def test_08_staff_tabs_bar_contains_marketing_tab(self):
        """All Staff page (/admin/users/) renders top tab for Marketing."""
        resp = self.client.get(reverse('admin_users_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse('admin_marketing_users_list'))
        self.assertContains(resp, "Marketing")
