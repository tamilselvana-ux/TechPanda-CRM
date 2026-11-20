import hmac
import hashlib
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import UserRole
from chat.models import BusinessAccount, Conversation, Message
from chat.serializers import BusinessAccountSerializer

User = get_user_model()


class MultiWhatsAppSecretsTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin_wa_secrets",
            email="admin_wa_secrets@example.com",
            password="testpassword123",
            role=UserRole.ADMIN
        )

        # Account A with dedicated secrets
        self.account_a = BusinessAccount.objects.create(
            name="Chennai Central Line",
            phone_number="+91 98765 00001",
            phone_number_id="100000000000001",
            business_account_id="waba_001",
            access_token="token_alpha_secret_xyz",
            app_secret="app_secret_alpha_11111",
            verify_token="verify_token_alpha_11111",
            automation_enabled=False,
            is_active=True
        )

        # Account B with dedicated secrets
        self.account_b = BusinessAccount.objects.create(
            name="Tambaram Branch Line",
            phone_number="+91 98765 00002",
            phone_number_id="100000000000002",
            business_account_id="waba_002",
            access_token="token_beta_secret_abc",
            app_secret="app_secret_beta_22222",
            verify_token="verify_token_beta_22222",
            automation_enabled=False,
            is_active=True
        )

    def test_business_account_storage_and_serializer_protection(self):
        # 1. Database verification
        acc = BusinessAccount.objects.get(id=self.account_a.id)
        self.assertEqual(acc.app_secret, "app_secret_alpha_11111")
        self.assertEqual(acc.verify_token, "verify_token_alpha_11111")
        self.assertEqual(acc.access_token, "token_alpha_secret_xyz")

        # 2. Write-only serializer protection: secrets must never leak in GET JSON
        serializer = BusinessAccountSerializer(acc)
        self.assertNotIn("app_secret", serializer.data)
        self.assertNotIn("verify_token", serializer.data)
        self.assertNotIn("access_token", serializer.data)
        self.assertEqual(serializer.data["name"], "Chennai Central Line")
        self.assertEqual(serializer.data["phone_number_id"], "100000000000001")

    def test_webhook_get_verification_with_per_account_tokens(self):
        webhook_url = reverse("whatsapp-webhook")

        # Test Account A verify token
        resp_a = self.client.get(webhook_url, {
            "hub.mode": "subscribe",
            "hub.challenge": "challenge_token_alpha_ok",
            "hub.verify_token": "verify_token_alpha_11111"
        })
        self.assertEqual(resp_a.status_code, 200)
        self.assertEqual(resp_a.content.decode("utf-8"), "challenge_token_alpha_ok")

        # Test Account B verify token
        resp_b = self.client.get(webhook_url, {
            "hub.mode": "subscribe",
            "hub.challenge": "challenge_token_beta_ok",
            "hub.verify_token": "verify_token_beta_22222"
        })
        self.assertEqual(resp_b.status_code, 200)
        self.assertEqual(resp_b.content.decode("utf-8"), "challenge_token_beta_ok")

        # Test invalid verify token
        resp_bad = self.client.get(webhook_url, {
            "hub.mode": "subscribe",
            "hub.challenge": "challenge_bad",
            "hub.verify_token": "completely_wrong_token"
        })
        self.assertEqual(resp_bad.status_code, 403)

    def test_webhook_post_signature_with_multiple_app_secrets(self):
        webhook_url = reverse("whatsapp-webhook")
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "waba_001",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "+91 98765 00001",
                                    "phone_number_id": "100000000000001"
                                },
                                "contacts": [{"wa_id": "919999999999", "profile": {"name": "Test Customer"}}],
                                "messages": [
                                    {
                                        "from": "919999999999",
                                        "id": "wamid.multi_secret_test_001",
                                        "timestamp": "1732080000",
                                        "type": "text",
                                        "text": {"body": "Testing multi-secret webhook dispatch"}
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        body_bytes = json.dumps(payload).encode("utf-8")

        # 1. Sign using Account A's dedicated app_secret
        sig_a = "sha256=" + hmac.new(b"app_secret_alpha_11111", body_bytes, hashlib.sha256).hexdigest()
        resp_a = self.client.post(
            webhook_url,
            data=body_bytes,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=sig_a
        )
        self.assertEqual(resp_a.status_code, 200)

        # 2. Sign using Account B's dedicated app_secret
        sig_b = "sha256=" + hmac.new(b"app_secret_beta_22222", body_bytes, hashlib.sha256).hexdigest()
        resp_b = self.client.post(
            webhook_url,
            data=body_bytes,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=sig_b
        )
        self.assertEqual(resp_b.status_code, 200)

        # 3. Reject bad signature
        sig_bad = "sha256=" + hmac.new(b"wrong_secret_attacker", body_bytes, hashlib.sha256).hexdigest()
        resp_bad = self.client.post(
            webhook_url,
            data=body_bytes,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=sig_bad
        )
        self.assertEqual(resp_bad.status_code, 403)

        # 4. Reject missing signature
        resp_missing = self.client.post(
            webhook_url,
            data=body_bytes,
            content_type="application/json"
        )
        self.assertEqual(resp_missing.status_code, 403)

    def test_patch_business_account_secrets_api(self):
        self.client.force_login(self.admin_user)
        detail_url = f"/api/business-accounts/{self.account_a.id}/"

        patch_data = {
            "name": "Updated Chennai Central Line",
            "app_secret": "new_app_secret_99999",
            "verify_token": "new_verify_token_99999",
            "access_token": "new_access_token_99999"
        }
        response = self.client.patch(
            detail_url,
            data=json.dumps(patch_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        acc = BusinessAccount.objects.get(id=self.account_a.id)
        self.assertEqual(acc.name, "Updated Chennai Central Line")
        self.assertEqual(acc.app_secret, "new_app_secret_99999")
        self.assertEqual(acc.verify_token, "new_verify_token_99999")
        self.assertEqual(acc.access_token, "new_access_token_99999")
