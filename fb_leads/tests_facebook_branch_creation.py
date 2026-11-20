from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from branches.models import Branch
from fb_leads.models import FacebookAccount, FacebookPage
from fb_leads.facebook import sync_pages_for_account


class FacebookBranchCreationTests(TestCase):
    """
    Test suite verifying that connecting a new Facebook Account requires
    and assigns a target CRM Branch to imported Facebook Pages.
    """

    def setUp(self):
        self.client = Client()
        self.branch_tn, _ = Branch.objects.get_or_create(name="T. Nagar", defaults={"status": "Active"})
        self.branch_vel, _ = Branch.objects.get_or_create(name="Velachery", defaults={"status": "Active"})

        self.admin = User.objects.create_superuser(
            username="admin_fb_branch",
            email="admin_fb@test.com",
            phone="9840299999",
            password="Password123!"
        )
        self.client.login(username="admin_fb_branch", password="Password123!")

    def test_fb_accounts_page_context_includes_branches(self):
        """Verify that Facebook Accounts management page renders with active branches list."""
        resp = self.client.get(reverse("fb_leads:fb_accounts"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("branches", resp.context)
        branch_names = [b.name for b in resp.context["branches"]]
        self.assertIn("T. Nagar", branch_names)
        self.assertIn("Velachery", branch_names)

    @patch("fb_leads.facebook.sync_pages_for_account")
    def test_fb_account_connect_passes_selected_branch(self, mock_sync):
        """Verify that connecting an account extracts target branch and passes to sync_pages_for_account."""
        mock_sync.return_value = 2

        resp = self.client.post(reverse("fb_leads:fb_account_connect"), {
            "account_name": "Test Agency Account",
            "access_token": "EAAG_TEST_TOKEN_123",
            "branch": str(self.branch_tn.id),
            "app_id": "999888777",
            "app_secret": "sec_test_123",
            "verify_token": "tok_test_123",
        })
        self.assertEqual(resp.status_code, 302)

        account = FacebookAccount.objects.get(account_name="Test Agency Account")
        self.assertEqual(account.app_id, "999888777")
        self.assertEqual(account.app_secret, "sec_test_123")
        self.assertEqual(account.verify_token, "tok_test_123")

        mock_sync.assert_called_once_with(account, default_branch=self.branch_tn)

    @patch("requests.get")
    def test_sync_pages_for_account_assigns_branch_to_imported_pages(self, mock_get):
        """Verify that sync_pages_for_account assigns default_branch to all discovered pages."""
        mock_get.return_value.json.return_value = {
            "data": [
                {
                    "id": "PAGE_ID_101",
                    "name": "TechPanda T. Nagar Main",
                    "access_token": "EAA_PAGE_TOKEN_101"
                },
                {
                    "id": "PAGE_ID_102",
                    "name": "TechPanda T. Nagar Admissions",
                    "access_token": "EAA_PAGE_TOKEN_102"
                }
            ]
        }

        account = FacebookAccount.objects.create(
            account_name="Direct Sync Account",
            access_token="EAA_USER_DIRECT",
            status="CONNECTED"
        )

        pages_count = sync_pages_for_account(account, default_branch=self.branch_vel)
        self.assertEqual(pages_count, 2)

        p1 = FacebookPage.objects.get(page_id="PAGE_ID_101")
        self.assertEqual(p1.branch, self.branch_vel)
        self.assertEqual(p1.page_name, "TechPanda T. Nagar Main")

        p2 = FacebookPage.objects.get(page_id="PAGE_ID_102")
        self.assertEqual(p2.branch, self.branch_vel)
        self.assertEqual(p2.page_name, "TechPanda T. Nagar Admissions")
