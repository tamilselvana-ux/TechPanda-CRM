from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, UserRole
from branches.models import Branch
from leads.models import Lead, LeadStatus


class MarketingStaffManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.branch_chennai, _ = Branch.objects.get_or_create(name='Chennai Main', defaults={'status': 'Active'})
        self.branch_madurai, _ = Branch.objects.get_or_create(name='Madurai Center', defaults={'status': 'Active'})

        # Superadmin user
        self.admin = User.objects.create_superuser(
            username='admin_staff_mgr',
            password='AdminPassword123!',
            email='admin_staff_mgr@test.com',
            role=UserRole.ADMIN
        )

        # Standard Marketing user
        self.marketing_user = User.objects.create_user(
            username='marketing_priya',
            password='StaffPassword123!',
            email='priya@marketing.test',
            first_name='Priya',
            last_name='Natarajan',
            phone='9840112233',
            role=UserRole.MARKETING,
            is_active=True,
            branch=self.branch_chennai
        )

        # Inactive Marketing user
        self.marketing_inactive = User.objects.create_user(
            username='marketing_karthik',
            password='StaffPassword123!',
            email='karthik@marketing.test',
            first_name='Karthik',
            last_name='Sundaram',
            phone='9840998877',
            role=UserRole.MARKETING,
            is_active=False,
            branch=None
        )

        # Regular non-admin staff
        self.telecaller = User.objects.create_user(
            username='tc_regular',
            password='StaffPassword123!',
            email='tc@test.com',
            role=UserRole.TELECALLER,
            is_active=True
        )

        # Create sample leads
        Lead.objects.create(name='Test Lead 1', phone='9000000001', status=LeadStatus.NEW)
        Lead.objects.create(name='Test Lead 2', phone='9000000002', status=LeadStatus.CONTACTED)

    def test_01_admin_marketing_users_list_view_renders_correctly(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_marketing_users_list'))
        self.assertEqual(response.status_code, 200)

        # Check content and table elements
        self.assertContains(response, 'MARKETING TEAM')
        self.assertContains(response, 'Priya Natarajan')
        self.assertContains(response, 'marketing_priya')
        self.assertContains(response, 'Karthik Sundaram')
        self.assertContains(response, 'marketing_karthik')

        # Action links
        self.assertContains(response, reverse('resend_user_invitation', args=[self.marketing_user.id]))
        self.assertContains(response, reverse('admin_set_user_password', args=[self.marketing_user.id]))
        self.assertContains(response, reverse('admin_marketing_user_edit', args=[self.marketing_user.id]))
        self.assertContains(response, reverse('admin_marketing_user_toggle_status', args=[self.marketing_user.id]))
        self.assertContains(response, reverse('admin_marketing_user_detail', args=[self.marketing_user.id]))

    def test_02_admin_marketing_users_list_search_and_branch_filter(self):
        self.client.force_login(self.admin)

        # Search by query
        res_search = self.client.get(reverse('admin_marketing_users_list') + '?q=Priya')
        self.assertEqual(res_search.status_code, 200)
        self.assertContains(res_search, 'Priya Natarajan')
        self.assertNotContains(res_search, 'Karthik Sundaram')

        # Filter by branch
        res_branch = self.client.get(reverse('admin_marketing_users_list') + f'?branch={self.branch_chennai.id}')
        self.assertEqual(res_branch.status_code, 200)
        self.assertContains(res_branch, 'Priya Natarajan')
        self.assertNotContains(res_branch, 'Karthik Sundaram')

        # Filter by status
        res_active = self.client.get(reverse('admin_marketing_users_list') + '?status=active')
        self.assertEqual(res_active.status_code, 200)
        self.assertContains(res_active, 'Priya Natarajan')
        self.assertNotContains(res_active, 'Karthik Sundaram')

    def test_03_admin_marketing_user_detail_view(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_marketing_user_detail', args=[self.marketing_user.id]))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Staff Profile &amp; Credentials')
        self.assertContains(response, 'Priya Natarajan')
        self.assertContains(response, '@marketing_priya')
        self.assertContains(response, 'priya@marketing.test')
        self.assertContains(response, 'Chennai Main')
        self.assertContains(response, 'Total Visible Leads')
        self.assertContains(response, 'Marketing Scope &amp; Repository')

    def test_04_admin_marketing_user_edit_view_get_and_post(self):
        self.client.force_login(self.admin)

        # GET edit page
        res_get = self.client.get(reverse('admin_marketing_user_edit', args=[self.marketing_user.id]))
        self.assertEqual(res_get.status_code, 200)
        self.assertContains(res_get, 'Edit Marketing Staff')

        # POST updates
        post_data = {
            'first_name': 'Priyanka',
            'last_name': 'Natarajan',
            'email': 'priyanka.updated@marketing.test',
            'phone': '9840999111',
            'branch': self.branch_madurai.id,
            'is_active': True,
        }
        res_post = self.client.post(reverse('admin_marketing_user_edit', args=[self.marketing_user.id]), data=post_data)
        self.assertRedirects(res_post, reverse('admin_marketing_user_detail', args=[self.marketing_user.id]))

        self.marketing_user.refresh_from_db()
        self.assertEqual(self.marketing_user.first_name, 'Priyanka')
        self.assertEqual(self.marketing_user.email, 'priyanka.updated@marketing.test')
        self.assertEqual(self.marketing_user.phone, '9840999111')
        self.assertEqual(self.marketing_user.branch, self.branch_madurai)

    def test_05_admin_marketing_user_toggle_status(self):
        self.client.force_login(self.admin)

        # Deactivate
        res_toggle = self.client.post(reverse('admin_marketing_user_toggle_status', args=[self.marketing_user.id]))
        self.assertRedirects(res_toggle, reverse('admin_marketing_users_list'))
        self.marketing_user.refresh_from_db()
        self.assertFalse(self.marketing_user.is_active)

        # Reactivate
        res_toggle2 = self.client.post(reverse('admin_marketing_user_toggle_status', args=[self.marketing_user.id]))
        self.assertRedirects(res_toggle2, reverse('admin_marketing_users_list'))
        self.marketing_user.refresh_from_db()
        self.assertTrue(self.marketing_user.is_active)

    def test_06_admin_set_user_password_redirects_for_marketing(self):
        self.client.force_login(self.admin)

        # POST valid password change
        new_pass_data = {
            'new_password1': 'NewSecurePassword2026!',
            'new_password2': 'NewSecurePassword2026!',
        }
        res_pass = self.client.post(reverse('admin_set_user_password', args=[self.marketing_user.id]), data=new_pass_data)
        self.assertRedirects(res_pass, reverse('admin_marketing_user_detail', args=[self.marketing_user.id]))

        # Verify password updated
        self.marketing_user.refresh_from_db()
        self.assertTrue(self.marketing_user.check_password('NewSecurePassword2026!'))

    def test_07_resend_user_invitation_redirects_for_marketing(self):
        self.client.force_login(self.admin)

        res_invite = self.client.post(reverse('resend_user_invitation', args=[self.marketing_user.id]))
        self.assertRedirects(res_invite, reverse('admin_marketing_users_list'))

    def test_08_universal_user_profile_redirect_for_marketing(self):
        self.client.force_login(self.admin)

        res = self.client.get(reverse('universal_user_profile', args=[self.marketing_user.id]))
        self.assertRedirects(res, reverse('admin_marketing_user_detail', args=[self.marketing_user.id]))

    def test_09_non_admin_cannot_access_marketing_management(self):
        self.client.force_login(self.telecaller)

        # Telecaller blocked from marketing staff management
        res_list = self.client.get(reverse('admin_marketing_users_list'))
        self.assertIn(res_list.status_code, [302, 403])

        res_detail = self.client.get(reverse('admin_marketing_user_detail', args=[self.marketing_user.id]))
        self.assertIn(res_detail.status_code, [302, 403])

        res_edit = self.client.get(reverse('admin_marketing_user_edit', args=[self.marketing_user.id]))
        self.assertIn(res_edit.status_code, [302, 403])
