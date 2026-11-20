from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from accounts.models import User, UserRole
from branches.models import Branch


class OneClickMetaSyncAPITests(TestCase):
    """
    Automated verification of One-Click Meta Accounts Synchronization endpoints
    for both WhatsApp lines and Facebook Lead Ads pages.
    """

    def setUp(self):
        self.client = Client()
        self.branch = Branch.objects.create(name="Anna Nagar Central", status="Active")

        self.admin = User.objects.create_superuser(
            username="admin_sync_tester",
            email="admin_sync@techpanda.test",
            phone="9876543201",
            password="AdminPassword123!"
        )
        self.telecaller = User.objects.create_user(
            username="telecaller_sync_tester",
            email="tc_sync@techpanda.test",
            phone="9876543202",
            password="UserPassword123!",
            role=UserRole.TELECALLER,
            branch=self.branch
        )

    @patch('services.env_meta_sync.sync_all_env_meta_accounts')
    def test_01_chat_sync_env_accounts_api_as_admin(self, mock_sync):
        """Admin can trigger POST /chat/api/sync-env-accounts/ and receives 200 OK with stats."""
        mock_sync.return_value = {
            "whatsapp_created": 3,
            "whatsapp_updated": 1,
            "facebook_created": 2,
            "facebook_updated": 0,
        }
        self.client.login(username="admin_sync_tester", password="AdminPassword123!")

        url = reverse('api-sync-env-accounts')
        resp = self.client.post(url, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['stats']['whatsapp_created'], 3)
        self.assertEqual(data['stats']['facebook_created'], 2)
        mock_sync.assert_called_once()

    def test_02_chat_sync_env_accounts_api_forbidden_for_telecaller(self):
        """Telecaller cannot trigger POST /chat/api/sync-env-accounts/ (403 Forbidden)."""
        self.client.login(username="telecaller_sync_tester", password="UserPassword123!")
        url = reverse('api-sync-env-accounts')
        resp = self.client.post(url, content_type='application/json')
        self.assertEqual(resp.status_code, 403)

    @patch('services.env_meta_sync.sync_all_env_meta_accounts')
    def test_03_fb_sync_env_accounts_endpoint_as_admin_ajax(self, mock_sync):
        """Admin can trigger POST /fb/accounts/sync-env/ via AJAX and receives 200 OK with stats."""
        mock_sync.return_value = {
            "whatsapp_created": 1,
            "whatsapp_updated": 2,
            "facebook_created": 4,
            "facebook_updated": 1,
        }
        self.client.login(username="admin_sync_tester", password="AdminPassword123!")

        url = reverse('fb_leads:fb_sync_env_accounts')
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn('stats', data)
        self.assertEqual(data['stats']['facebook_created'], 4)
        mock_sync.assert_called_once()

    def test_04_fb_sync_env_accounts_endpoint_forbidden_for_telecaller(self):
        """Telecaller cannot trigger POST /fb/accounts/sync-env/ (403 Forbidden)."""
        self.client.login(username="telecaller_sync_tester", password="UserPassword123!")
        url = reverse('fb_leads:fb_sync_env_accounts')
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 403)
