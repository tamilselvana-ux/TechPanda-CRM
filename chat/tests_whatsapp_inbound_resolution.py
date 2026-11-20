"""
Automated Verification Test Suite for WhatsApp Inbound Webhook Routing,
Multi-Account Secret Parsing, and Ingestion Resolution.
Zero emojis used throughout.
"""

import hmac
import hashlib
import json
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from chat.models import BusinessAccount, Conversation, Message


class WhatsAppInboundResolutionTests(TestCase):
    """
    Validates resilient webhook routing, HMAC multi-secret matching,
    and inbound message ingestion for WhatsApp Cloud API.
    """

    def setUp(self):
        self.client = Client()
        self.secret_1 = "fd6316e5e9e5eebedc5d0d6936484d4a"
        self.secret_2 = "50bb27751fdd0cfb887dd4db5e54dab8"
        self.verify_token = "techpanda-crm-2026"

        self.biz_account = BusinessAccount.objects.create(
            name="Main WhatsApp Line",
            phone_number="+918438239448",
            phone_number_id="129416667",
            app_secret=self.secret_1,
            verify_token=self.verify_token,
            is_active=True,
            is_default=True,
        )

    def _sign_payload(self, payload_bytes: bytes, secret: str) -> str:
        return "sha256=" + hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    def test_get_webhook_verification_handshake_all_aliases(self):
        """
        Meta Graph API must receive the hub.challenge across all registered webhook aliases.
        """
        urls_to_test = [
            "/webhook/whatsapp/",
            "/webhook/",
            "/chat/webhook/",
            "/whatsapp/webhook/",
        ]
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": self.verify_token,
            "hub.challenge": "1158201444",
        }
        for url in urls_to_test:
            response = self.client.get(url, params)
            self.assertEqual(
                response.status_code,
                200,
                f"Failed GET handshake on {url}: status {response.status_code}",
            )
            self.assertEqual(response.content.decode("utf-8"), "1158201444")

    def test_get_webhook_verification_invalid_token(self):
        """
        Webhook verification must be rejected with 403 when verify token does not match.
        """
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_invalid_token",
            "hub.challenge": "1158201444",
        }
        response = self.client.get("/webhook/whatsapp/", params)
        self.assertEqual(response.status_code, 403)

    def test_post_inbound_message_with_secret_1(self):
        """
        Inbound user message signed with Secret 1 must be ingested into DB as customer message.
        """
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "129416667",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "918438239448",
                                    "phone_number_id": "129416667",
                                },
                                "contacts": [
                                    {
                                        "profile": {"name": "Test Customer Inbound"},
                                        "wa_id": "919876543210",
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "919876543210",
                                        "id": "wamid.HBgNNTE5ODc2NTQzMjEwFQIAEhgUM0EBNDgwQzM2REQ5M0IzODNFOAA=",
                                        "timestamp": "1732100000",
                                        "text": {"body": "Hello CRM, can you hear me?"},
                                        "type": "text",
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        signature = self._sign_payload(body_bytes, self.secret_1)

        response = self.client.post(
            "/webhook/whatsapp/",
            data=body_bytes,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=signature,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), "EVENT_RECEIVED")

        # Verify Message and Conversation created
        conv = Conversation.objects.filter(phone_number="+919876543210").first()
        self.assertIsNotNone(conv, "Conversation was not created for inbound message")
        self.assertEqual(conv.customer_name, "Test Customer Inbound")
        self.assertEqual(conv.unread_count, 1)

        msg = Message.objects.filter(conversation=conv).first()
        self.assertIsNotNone(msg, "Message was not saved for inbound message")
        self.assertEqual(msg.sender, Message.SENDER_CUSTOMER)
        self.assertEqual(msg.message_text, "Hello CRM, can you hear me?")
        self.assertEqual(msg.status, Message.STATUS_DELIVERED)

    def test_post_inbound_message_with_comma_separated_env_secret(self):
        """
        Inbound message signed with second secret in a comma-separated list must also pass HMAC.
        """
        with override_settings(WHATSAPP_APP_SECRET=f"{self.secret_1}, {self.secret_2}"):
            payload = {
                "object": "whatsapp_business_account",
                "entry": [
                    {
                        "id": "129416667",
                        "changes": [
                            {
                                "field": "messages",
                                "value": {
                                    "messaging_product": "whatsapp",
                                    "metadata": {
                                        "display_phone_number": "918438239448",
                                        "phone_number_id": "129416667",
                                    },
                                    "contacts": [
                                        {
                                            "profile": {"name": "Second Developer Lead"},
                                            "wa_id": "919999988888",
                                        }
                                    ],
                                    "messages": [
                                        {
                                            "from": "919999988888",
                                            "id": "wamid.SECOND_DEV_TEST_001",
                                            "timestamp": "1732100010",
                                            "text": {"body": "Testing second account secret"},
                                            "type": "text",
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                ],
            }
            body_bytes = json.dumps(payload).encode("utf-8")
            signature = self._sign_payload(body_bytes, self.secret_2)

            response = self.client.post(
                "/webhook/",
                data=body_bytes,
                content_type="application/json",
                HTTP_X_HUB_SIGNATURE_256=signature,
            )
            self.assertEqual(response.status_code, 200)

            conv = Conversation.objects.filter(phone_number="+919999988888").first()
            self.assertIsNotNone(conv)
            msg = Message.objects.filter(whatsapp_message_id="wamid.SECOND_DEV_TEST_001").first()
            self.assertIsNotNone(msg)
            self.assertEqual(msg.message_text, "Testing second account secret")

    def test_post_webhook_missing_or_bad_signature(self):
        """
        POST request with missing or incorrect signature must be rejected with 403.
        """
        payload = {"dummy": "payload"}
        body_bytes = json.dumps(payload).encode("utf-8")

        # Missing header
        res_missing = self.client.post(
            "/webhook/whatsapp/",
            data=body_bytes,
            content_type="application/json",
        )
        self.assertEqual(res_missing.status_code, 403)

        # Invalid header
        res_invalid = self.client.post(
            "/webhook/whatsapp/",
            data=body_bytes,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256="sha256=invalidhashvalue1234567890",
        )
        self.assertEqual(res_invalid.status_code, 403)
