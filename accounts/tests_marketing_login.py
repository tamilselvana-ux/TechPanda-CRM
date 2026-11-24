from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User, UserRole
from branches.models import Branch


class MarketingLoginAndDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.branch = Branch.objects.filter(name="T-Nagar").first() or Branch.objects.create(name="T-Nagar", status="Active")
        self.marketing_user = User.objects.create_user(
            username="marketing_tester",
            email="marketing_tester@techpanda.test",
            password="SecurePassword123!",
            role=UserRole.MARKETING,
            branch=self.branch,
        )
        self.admin_user = User.objects.create_superuser(
            username="admin_tester",
            email="admin_tester@techpanda.test",
            password="AdminPassword123!",
            role=UserRole.ADMIN,
            branch=self.branch,
        )

    def test_marketing_user_login_redirect(self):
        """Marketing user logs in and is redirected to marketing_dashboard."""
        self.client.force_login(self.marketing_user)
        res = self.client.get(reverse('login_redirect'))
        self.assertRedirects(res, reverse('marketing_dashboard'))

    def test_marketing_dashboard_renders_for_marketing_user(self):
        """Marketing user can view marketing_dashboard with 200 OK and navigation, including linked FB leads."""
        from leads.models import Lead
        from fb_leads.models import FacebookLead, FacebookPage, FacebookAccount
        account = FacebookAccount.objects.create(account_name="Test Meta Account", access_token="test_tok")
        page = FacebookPage.objects.create(account=account, page_id="123456789", page_name="Test Page", page_access_token="test_tok")
        lead = Lead.objects.create(name="Student Candidate", phone="9988776655", branch=self.branch)
        FacebookLead.objects.create(
            leadgen_id="fb_lead_123",
            lead=lead,
            fb_page=page,
            form_id="form_1",
            form_name="Full Stack Course",
            full_name="Student Candidate",
            phone="9988776655",
        )

        self.client.force_login(self.marketing_user)
        res = self.client.get(reverse('marketing_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Marketing Workspace')
        self.assertContains(res, 'Facebook Leads')
        self.assertContains(res, 'WhatsApp Campaigns')
        self.assertContains(res, 'Meta Connections')
        self.assertContains(res, reverse('admin_lead_detail', args=[lead.id]))
        self.assertContains(res, 'Student Candidate')

    def test_marketing_user_sidebar_navigation(self):
        """Sidebar renders marketing-specific links when logged in as marketing."""
        self.client.force_login(self.marketing_user)
        res = self.client.get(reverse('marketing_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Marketing Workspace')
        self.assertContains(res, reverse('marketing_dashboard'))
        self.assertContains(res, reverse('fb_leads:facebook_leads'))
        self.assertContains(res, reverse('fb_leads:fb_accounts'))
        self.assertContains(res, reverse('whatsapp_campaigns_list'))

    def test_marketing_user_can_access_facebook_leads(self):
        """Marketing user has permission to view Facebook leads list."""
        self.client.force_login(self.marketing_user)
        res = self.client.get(reverse('fb_leads:facebook_leads'))
        self.assertEqual(res.status_code, 200)

    def test_marketing_user_can_access_whatsapp_campaigns(self):
        """Marketing user has permission to view WhatsApp campaigns."""
        self.client.force_login(self.marketing_user)
        res = self.client.get(reverse('whatsapp_campaigns_list'))
        self.assertEqual(res.status_code, 200)

    def test_marketing_user_cannot_access_admin_marketing_staff_list(self):
        """Marketing user cannot access the admin-only staff management list."""
        self.client.force_login(self.marketing_user)
        res = self.client.get(reverse('admin_marketing_users_list'))
        # Should redirect back to their dashboard or deny access
        self.assertIn(res.status_code, [302, 403])
        if res.status_code == 302:
            self.assertRedirects(res, reverse('marketing_dashboard'))
