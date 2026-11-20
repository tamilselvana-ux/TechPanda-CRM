import os
import hmac
import hashlib
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from branches.models import Branch
from fb_leads.models import FacebookAccount, FacebookPage
from services.env_meta_sync import (
    parse_facebook_env_pages,
    sync_all_env_meta_accounts,
)


class MultiDeveloperFacebookEnvSyncTests(TestCase):
    """
    Test suite verifying multi-developer environment Facebook pages synchronization,
    database provisioning, and multi-secret Facebook Lead Ads webhook verification.
    """

    def setUp(self):
        self.client = Client()
        self.branch_tn, _ = Branch.objects.get_or_create(name="T. Nagar", defaults={"status": "Active"})
        self.branch_vel, _ = Branch.objects.get_or_create(name="Velachery", defaults={"status": "Active"})

    def test_parse_numbered_facebook_pages(self):
        """Verify extraction of multiple numbered Facebook pages from environment."""
        env_dict = {
            "FB_PAGE_1_ACCOUNT_NAME": "Dev Account 1",
            "FB_PAGE_1_NAME": "T. Nagar Page",
            "FB_PAGE_1_PAGE_ID": "30001",
            "FB_PAGE_1_TOKEN": "token_fb_1",
            "FB_PAGE_1_APP_ID": "40001",
            "FB_PAGE_1_APP_SECRET": "sec_fb_1",
            "FB_PAGE_1_VERIFY_TOKEN": "ver_fb_1",
            "FB_PAGE_1_BRANCH": "T. Nagar",
            "FB_PAGE_2_ACCOUNT_NAME": "Dev Account 2",
            "FB_PAGE_2_NAME": "Velachery Page",
            "FB_PAGE_2_PAGE_ID": "30002",
            "FB_PAGE_2_TOKEN": "token_fb_2",
            "FB_PAGE_2_APP_ID": "40002",
            "FB_PAGE_2_APP_SECRET": "sec_fb_2",
            "FB_PAGE_2_VERIFY_TOKEN": "ver_fb_2",
            "FB_PAGE_2_BRANCH": "Velachery",
        }
        with patch.dict(os.environ, env_dict, clear=False):
            pages = parse_facebook_env_pages()
            page_ids = [p["page_id"] for p in pages]
            self.assertIn("30001", page_ids)
            self.assertIn("30002", page_ids)

    def test_sync_all_env_meta_accounts_facebook(self):
        """Verify automated database provisioning of Facebook accounts and pages from environment."""
        env_dict = {
            "FB_PAGE_1_ACCOUNT_NAME": "Sync Account 1",
            "FB_PAGE_1_NAME": "Sync Page 1",
            "FB_PAGE_1_PAGE_ID": "50001",
            "FB_PAGE_1_TOKEN": "token_sync_1",
            "FB_PAGE_1_APP_ID": "60001",
            "FB_PAGE_1_APP_SECRET": "sec_sync_1",
            "FB_PAGE_1_VERIFY_TOKEN": "ver_sync_1",
            "FB_PAGE_1_BRANCH": "T. Nagar",
        }
        with patch.dict(os.environ, env_dict, clear=False):
            stats = sync_all_env_meta_accounts()
            self.assertGreaterEqual(stats["facebook_created"], 1)

            p1 = FacebookPage.objects.get(page_id="50001")
            self.assertEqual(p1.page_name, "Sync Page 1")
            self.assertEqual(p1.branch, self.branch_tn)
            self.assertEqual(p1.account.app_id, "60001")
            self.assertEqual(p1.account.app_secret, "sec_sync_1")
            self.assertEqual(p1.account.verify_token, "ver_sync_1")

            # Second execution should update without creating duplicates
            stats2 = sync_all_env_meta_accounts()
            self.assertEqual(stats2["facebook_created"], 0)

    def test_facebook_webhook_get_verification_with_candidate_tokens(self):
        """Verify Facebook Lead Ads webhook GET handshake accepts tokens from multi-developer env."""
        env_dict = {
            "FB_VERIFY_TOKENS": "fb_token_dev_1, fb_token_dev_2, fb_token_dev_3",
            "FB_PAGE_4_VERIFY_TOKEN": "fb_token_numbered_dev_4",
        }
        with patch.dict(os.environ, env_dict, clear=False):
            # Token from comma-separated list
            resp1 = self.client.get(reverse("fb_leads:facebook_leads_webhook"), {
                "hub.mode": "subscribe",
                "hub.verify_token": "fb_token_dev_2",
                "hub.challenge": "challenge_fb_123"
            })
            self.assertEqual(resp1.status_code, 200)
            self.assertEqual(resp1.content.decode("utf-8"), "challenge_fb_123")

            # Token from numbered env variable
            resp2 = self.client.get(reverse("fb_leads:facebook_leads_webhook"), {
                "hub.mode": "subscribe",
                "hub.verify_token": "fb_token_numbered_dev_4",
                "hub.challenge": "challenge_fb_456"
            })
            self.assertEqual(resp2.status_code, 200)
            self.assertEqual(resp2.content.decode("utf-8"), "challenge_fb_456")

            # Invalid token returns 403
            resp3 = self.client.get(reverse("fb_leads:facebook_leads_webhook"), {
                "hub.mode": "subscribe",
                "hub.verify_token": "invalid_fb_token",
                "hub.challenge": "challenge_fb_fail"
            })
            self.assertEqual(resp3.status_code, 403)

    def test_facebook_webhook_post_signature_with_multiple_secrets(self):
        """Verify Facebook Lead Ads webhook POST accepts valid signatures across developer app secrets."""
        secret_fb_a = "secret_meta_dev_app_a"
        secret_fb_b = "secret_meta_dev_app_b"
        env_dict = {
            "FB_APP_SECRETS": f"{secret_fb_a}, {secret_fb_b}",
        }
        with patch.dict(os.environ, env_dict, clear=False):
            payload = b'{"object": "page", "entry": []}'

            # Signature signed by App Secret A
            sig_a = "sha256=" + hmac.new(secret_fb_a.encode("utf-8"), payload, hashlib.sha256).hexdigest()
            resp_a = self.client.post(
                reverse("fb_leads:facebook_leads_webhook"),
                data=payload,
                content_type="application/json",
                HTTP_X_HUB_SIGNATURE_256=sig_a
            )
            self.assertEqual(resp_a.status_code, 200)

            # Signature signed by App Secret B
            sig_b = "sha256=" + hmac.new(secret_fb_b.encode("utf-8"), payload, hashlib.sha256).hexdigest()
            resp_b = self.client.post(
                reverse("fb_leads:facebook_leads_webhook"),
                data=payload,
                content_type="application/json",
                HTTP_X_HUB_SIGNATURE_256=sig_b
            )
            self.assertEqual(resp_b.status_code, 200)

            # Forged signature returns 403
            resp_bad = self.client.post(
                reverse("fb_leads:facebook_leads_webhook"),
                data=payload,
                content_type="application/json",
                HTTP_X_HUB_SIGNATURE_256="sha256=ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            )
            self.assertEqual(resp_bad.status_code, 403)
