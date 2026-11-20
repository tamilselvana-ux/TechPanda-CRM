from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, UserRole
from branches.models import Branch


class StaffUILayoutAndDOMTests(TestCase):
    """
    Automated verification of Staff & Role management views:
    - DOM tag balancing and page header termination
    - KPI cards rendering
    - Filter card layout and Filter submit button existence
    - Clean HTTP 200 responses without layout distortion
    """

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username="admin_layout_test",
            email="admin_layout@example.com",
            phone="9988776655",
            password="Password123!"
        )
        self.client.login(username="admin_layout_test", password="Password123!")

        self.branch = Branch.objects.create(name="Anna Nagar Central", status="Active")

        # Create sample staff
        self.branch_admin = User.objects.create_user(
            username="ba_user_test",
            email="ba@example.com",
            phone="9840112233",
            password="Password123!",
            role=UserRole.BRANCH_ADMIN,
            branch=self.branch,
            is_active=True
        )
        self.receptionist = User.objects.create_user(
            username="rec_user_test",
            email="rec@example.com",
            phone="9840223344",
            password="Password123!",
            role=UserRole.RECEPTIONIST,
            branch=self.branch,
            is_active=True
        )
        self.accountant = User.objects.create_user(
            username="acc_user_test",
            email="acc@example.com",
            phone="9840334455",
            password="Password123!",
            role=UserRole.ACCOUNTANT,
            branch=self.branch,
            is_active=True
        )

    def test_01_branch_admins_list_layout_and_header(self):
        """Verify Branch Admins view has closed page-header and full-width KPI cards."""
        resp = self.client.get(reverse('admin_branch_admins_list'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')

        # Verify page header closed before role tabs
        header_idx = content.find('class="page-header"')
        header_pos = content.rfind('<div', 0, header_idx)
        tabs_pos = content.find('TEAM & STAFF ROLE TABS BAR')
        self.assertGreater(header_pos, -1)
        self.assertGreater(tabs_pos, header_pos)

        # In between header and tabs, page-header must be closed
        header_chunk = content[header_pos:tabs_pos]
        self.assertEqual(header_chunk.count('<div'), header_chunk.count('</div>'))

        # Verify KPI cards present
        self.assertIn('Total Branch Admins', content)
        self.assertIn('Active Status', content)
        self.assertIn('Active Branches', content)

    def test_02_receptionists_list_layout_and_filter_button(self):
        """Verify Receptionists view has closed page-header and Filter submit button."""
        resp = self.client.get(reverse('admin_receptionists_list'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')

        header_idx = content.find('class="page-header"')
        header_pos = content.rfind('<div', 0, header_idx)
        tabs_pos = content.find('TEAM & STAFF ROLE TABS BAR')
        self.assertGreater(header_pos, -1)
        self.assertGreater(tabs_pos, header_pos)

        header_chunk = content[header_pos:tabs_pos]
        self.assertEqual(header_chunk.count('<div'), header_chunk.count('</div>'))

        # Verify Filter submit button is present in the form
        self.assertIn('type="submit"', content)
        self.assertIn('Filter', content)
        self.assertIn('Reset', content)

    def test_03_accountants_list_layout_and_header(self):
        """Verify Accountants view has closed page-header and balanced divs."""
        resp = self.client.get(reverse('admin_accountants_list'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')

        header_idx = content.find('class="page-header"')
        header_pos = content.rfind('<div', 0, header_idx)
        tabs_pos = content.find('TEAM & STAFF ROLE TABS BAR')
        self.assertGreater(header_pos, -1)
        self.assertGreater(tabs_pos, header_pos)

        header_chunk = content[header_pos:tabs_pos]
        self.assertEqual(header_chunk.count('<div'), header_chunk.count('</div>'))

    def test_04_channels_list_view(self):
        """Verify Channels view returns HTTP 200 and renders cleanly."""
        resp = self.client.get(reverse('admin_channels_list'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        self.assertIn('Lead Channels', content)

    def test_05_receptionists_filter_submission(self):
        """Verify filtering receptionists by search and branch works as expected."""
        # Filter by branch
        resp_branch = self.client.get(reverse('admin_receptionists_list') + f'?branch={self.branch.id}')
        self.assertEqual(resp_branch.status_code, 200)
        self.assertIn('rec_user_test', resp_branch.content.decode('utf-8'))

        # Filter by search
        resp_search = self.client.get(reverse('admin_receptionists_list') + '?search=rec_user')
        self.assertEqual(resp_search.status_code, 200)
        self.assertIn('rec_user_test', resp_search.content.decode('utf-8'))
