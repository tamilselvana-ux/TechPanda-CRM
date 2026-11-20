import os
import hmac
import hashlib
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from branches.models import Branch
from chat.models import BusinessAccount
from services.env_meta_sync import (
    split_env_list,
    get_candidate_webhook_secrets,
    get_candidate_verify_tokens,
    parse_whatsapp_env_accounts,
    sync_all_env_meta_accounts,
)
from chat.whatsapp.webhook import verify_webhook_token


class MultiDeveloperEnvSyncTests(TestCase):
    """
    Test suite verifying multi-developer environment account synchronization,
    database provisioning, and multi-secret WhatsApp webhook verification.
    """

    def setUp(self):
        self.client = Client()
        self.branch_tn, _ = Branch.objects.get_or_create(name="T. Nagar", defaults={"status": "Active"})
        self.branch_vel, _ = Branch.objects.get_or_create(name="Velachery", defaults={"status": "Active"})
        self.branch_cbe, _ = Branch.objects.get_or_create(name="Coimbatore", defaults={"status": "Active"})

    def test_split_env_list(self):
        """Verify parsing of comma, semicolon, and newline delimited lists."""
        raw = "secret1, secret2; secret3\nsecret4 , secret1"
        tokens = split_env_list(raw)
        self.assertEqual(len(tokens), 4)
        self.assertEqual(tokens, ["secret1", "secret2", "secret3", "secret4"])

    def test_parse_numbered_whatsapp_accounts(self):
        """Verify extraction of 8+ numbered WhatsApp developer accounts from environment."""
        env_dict = {
            "WHATSAPP_1_NAME": "T. Nagar Line",
            "WHATSAPP_1_PHONE_ID": "10001",
            "WHATSAPP_1_ACCESS_TOKEN": "token_1",
            "WHATSAPP_1_APP_SECRET": "sec_1",
            "WHATSAPP_1_VERIFY_TOKEN": "tok_1",
            "WHATSAPP_1_BRANCH": "T. Nagar",
            "WHATSAPP_2_NAME": "Velachery Line",
            "WHATSAPP_2_PHONE_ID": "10002",
            "WHATSAPP_2_ACCESS_TOKEN": "token_2",
            "WHATSAPP_2_APP_SECRET": "sec_2",
            "WHATSAPP_2_VERIFY_TOKEN": "tok_2",
            "WHATSAPP_2_BRANCH": "Velachery",
            "WHATSAPP_8_NAME": "Coimbatore Line",
            "WHATSAPP_8_PHONE_ID": "10008",
            "WHATSAPP_8_ACCESS_TOKEN": "token_8",
            "WHATSAPP_8_APP_SECRET": "sec_8",
            "WHATSAPP_8_VERIFY_TOKEN": "tok_8",
            "WHATSAPP_8_BRANCH": "Coimbatore",
        }
        with patch.dict(os.environ, env_dict, clear=False):
            accounts = parse_whatsapp_env_accounts()
            phone_ids = [a["phone_number_id"] for a in accounts]
            self.assertIn("10001", phone_ids)
            self.assertIn("10002", phone_ids)
            self.assertIn("10008", phone_ids)

    def test_sync_all_env_meta_accounts_whatsapp(self):
        """Verify automated database provisioning from environment configs."""
        env_dict = {
            "WHATSAPP_1_NAME": "Auto Line 1",
            "WHATSAPP_1_PHONE_ID": "20001",
            "WHATSAPP_1_ACCESS_TOKEN": "tok_auto_1",
            "WHATSAPP_1_APP_SECRET": "sec_auto_1",
            "WHATSAPP_1_VERIFY_TOKEN": "ver_auto_1",
            "WHATSAPP_1_BRANCH": "T. Nagar",
            "WHATSAPP_2_NAME": "Auto Line 2",
            "WHATSAPP_2_PHONE_ID": "20002",
            "WHATSAPP_2_ACCESS_TOKEN": "tok_auto_2",
            "WHATSAPP_2_APP_SECRET": "sec_auto_2",
            "WHATSAPP_2_VERIFY_TOKEN": "ver_auto_2",
            "WHATSAPP_2_BRANCH": "Velachery",
        }
        with patch.dict(os.environ, env_dict, clear=False):
            stats = sync_all_env_meta_accounts()
            self.assertGreaterEqual(stats["whatsapp_created"], 2)

            ba1 = BusinessAccount.objects.get(phone_number_id="20001")
            self.assertEqual(ba1.name, "Auto Line 1")
            self.assertEqual(ba1.crm_branch, self.branch_tn)
            self.assertEqual(ba1.app_secret, "sec_auto_1")

            ba2 = BusinessAccount.objects.get(phone_number_id="20002")
            self.assertEqual(ba2.name, "Auto Line 2")
            self.assertEqual(ba2.crm_branch, self.branch_vel)
            self.assertEqual(ba2.verify_token, "ver_auto_2")

            # Second execution should update without creating duplicates
            stats2 = sync_all_env_meta_accounts()
            self.assertEqual(stats2["whatsapp_created"], 0)

    def test_whatsapp_webhook_get_verification_with_candidate_tokens(self):
        """Verify webhook handshake succeeds with candidate tokens from multi-developer env."""
        env_dict = {
            "WHATSAPP_VERIFY_TOKENS": "shared_token_dev_1, shared_token_dev_2, shared_token_dev_3",
            "WHATSAPP_5_VERIFY_TOKEN": "numbered_token_dev_5",
        }
        with patch.dict(os.environ, env_dict, clear=False):
            # Token from comma-separated list
            resp1 = self.client.get(reverse("whatsapp-webhook"), {
                "hub.mode": "subscribe",
                "hub.verify_token": "shared_token_dev_2",
                "hub.challenge": "challenge_abc_123"
            })
            self.assertEqual(resp1.status_code, 200)
            self.assertEqual(resp1.content.decode("utf-8"), "challenge_abc_123")

            # Token from numbered env variable
            resp2 = self.client.get(reverse("whatsapp-webhook"), {
                "hub.mode": "subscribe",
                "hub.verify_token": "numbered_token_dev_5",
                "hub.challenge": "challenge_xyz_789"
            })
            self.assertEqual(resp2.status_code, 200)
            self.assertEqual(resp2.content.decode("utf-8"), "challenge_xyz_789")

            # Invalid token
            resp3 = self.client.get(reverse("whatsapp-webhook"), {
                "hub.mode": "subscribe",
                "hub.verify_token": "completely_invalid_token",
                "hub.challenge": "challenge_rejected"
            })
            self.assertEqual(resp3.status_code, 403)

    def test_whatsapp_webhook_post_signature_with_multiple_secrets(self):
        """Verify webhook POST accepts valid signatures from any developer app secret."""
        secret_dev_a = "secret_developer_account_alpha"
        secret_dev_b = "secret_developer_account_beta"
        env_dict = {
            "WHATSAPP_APP_SECRETS": f"{secret_dev_a}, {secret_dev_b}",
        }
        with patch.dict(os.environ, env_dict, clear=False):
            payload = b'{"object": "whatsapp_business_account", "entry": []}'

            # Signature signed by Account A secret
            sig_a = "sha256=" + hmac.new(secret_dev_a.encode("utf-8"), payload, hashlib.sha256).hexdigest()
            resp_a = self.client.post(
                reverse("whatsapp-webhook"),
                data=payload,
                content_type="application/json",
                HTTP_X_HUB_SIGNATURE_256=sig_a
            )
            self.assertEqual(resp_a.status_code, 200)

            # Signature signed by Account B secret
            sig_b = "sha256=" + hmac.new(secret_dev_b.encode("utf-8"), payload, hashlib.sha256).hexdigest()
            resp_b = self.client.post(
                reverse("whatsapp-webhook"),
                data=payload,
                content_type="application/json",
                HTTP_X_HUB_SIGNATURE_256=sig_b
            )
            self.assertEqual(resp_b.status_code, 200)

            # Forged/invalid signature
            resp_bad = self.client.post(
                reverse("whatsapp-webhook"),
                data=payload,
                content_type="application/json",
                HTTP_X_HUB_SIGNATURE_256="sha256=0000000000000000000000000000000000000000000000000000000000000000"
            )
            self.assertEqual(resp_bad.status_code, 403)
