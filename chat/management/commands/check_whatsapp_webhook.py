import os
import json
import hmac
import hashlib
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = "Diagnoses WhatsApp Cloud API inbound webhook configuration, MySQL database state, and HMAC signatures."

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone-id',
            type=str,
            default='',
            help='Specific WhatsApp Phone Number ID to test.'
        )

    def handle(self, *args, **options):
        self.stdout.write("==================================================")
        self.stdout.write(" WHATSAPP WEBHOOK & MYSQL SERVER DIAGNOSTIC")
        self.stdout.write("==================================================\n")

        # 1. Database Connection & MySQL Column Check
        self.stdout.write("[1] Checking Database Connection & Schema...")
        db_engine = settings.DATABASES['default']['ENGINE']
        db_name = settings.DATABASES['default']['NAME']
        self.stdout.write(f"    Engine: {db_engine}")
        self.stdout.write(f"    Database Name: {db_name}")

        has_chat_migrations = True
        try:
            with connection.cursor() as cursor:
                # Check if chat_businessaccount exists
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'chat_businessaccount';")
                columns = [row[0].lower() for row in cursor.fetchall()]
                if not columns:
                    # SQLite fallback query
                    cursor.execute("PRAGMA table_info(chat_businessaccount);")
                    columns = [row[1].lower() for row in cursor.fetchall()]

                self.stdout.write(f"    chat_businessaccount columns found: {len(columns)}")
                missing_cols = []
                for req_col in ['app_secret', 'verify_token', 'phone_number_id', 'is_active']:
                    if req_col not in columns:
                        missing_cols.append(req_col)

                if missing_cols:
                    self.stdout.write(self.style.ERROR(f"    FAIL: Missing columns in chat_businessaccount: {missing_cols}"))
                    self.stdout.write(self.style.WARNING("    ACTION REQUIRED: Run 'python manage.py migrate chat' on this server!"))
                    has_chat_migrations = False
                else:
                    self.stdout.write(self.style.SUCCESS("    PASS: chat_businessaccount schema is up to date."))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"    Database schema introspection note: {exc}"))

        # 2. Check Stored Business Accounts in Database
        self.stdout.write("\n[2] Checking Business Accounts in Database...")
        try:
            from chat.models import BusinessAccount
            accounts = BusinessAccount.objects.all()
            self.stdout.write(f"    Total Business Accounts in DB: {accounts.count()}")
            for acc in accounts:
                self.stdout.write(
                    f"    - ID: {acc.id} | Name: '{acc.name}' | Phone ID: {acc.phone_number_id} | "
                    f"Active: {acc.is_active} | Secret set: {bool(acc.app_secret)} | Verify Token set: {bool(acc.verify_token)}"
                )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"    Could not read BusinessAccount table: {exc}"))

        # 3. Environment Variable Resolution
        self.stdout.write("\n[3] Checking Environment Variables & Candidate Secrets...")
        try:
            from services.env_meta_sync import get_candidate_webhook_secrets, get_candidate_verify_tokens
            candidate_secrets = get_candidate_webhook_secrets(provider="whatsapp")
            candidate_tokens = get_candidate_verify_tokens(provider="whatsapp")
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"    env_meta_sync warning: {exc}"))
            candidate_secrets = set()
            candidate_tokens = set()

        # Add fallback from settings
        if getattr(settings, 'WHATSAPP_APP_SECRET', ''):
            candidate_secrets.add(settings.WHATSAPP_APP_SECRET)
        if getattr(settings, 'WHATSAPP_VERIFY_TOKEN', ''):
            candidate_tokens.add(settings.WHATSAPP_VERIFY_TOKEN)

        self.stdout.write(f"    Resolved Candidate App Secrets: {len(candidate_secrets)}")
        self.stdout.write(f"    Resolved Candidate Verify Tokens: {len(candidate_tokens)} ({list(candidate_tokens)})")

        if not candidate_secrets:
            self.stdout.write(self.style.ERROR("    FAIL: No WhatsApp App Secrets configured in .env or database!"))
            self.stdout.write("    Incoming messages will be rejected with HTTP 403 'Bad signature'.")
        else:
            self.stdout.write(self.style.SUCCESS("    PASS: App Secrets are loaded and ready for HMAC verification."))

        # 4. Webhook Verification Handshake Test (GET)
        self.stdout.write("\n[4] Simulating Meta Webhook Verification Handshake (GET)...")
        from chat.views import WhatsAppWebhookView
        factory = RequestFactory()

        test_token = list(candidate_tokens)[0] if candidate_tokens else "whatsapp_crm_verify_token_secure"
        get_request = factory.get(
            '/webhook/whatsapp/',
            {
                'hub.mode': 'subscribe',
                'hub.verify_token': test_token,
                'hub.challenge': '1158201444'
            }
        )
        get_response = WhatsAppWebhookView.as_view()(get_request)
        if get_response.status_code == 200 and get_response.content.decode('utf-8') == '1158201444':
            self.stdout.write(self.style.SUCCESS(f"    PASS: Meta handshake succeeded with verify_token='{test_token}' (HTTP 200)."))
        else:
            self.stdout.write(self.style.ERROR(f"    FAIL: Meta handshake failed with status {get_response.status_code}: {get_response.content}"))

        # 5. Simulated Incoming Message Ingestion Test (POST)
        self.stdout.write("\n[5] Simulating Meta Incoming Message Ingestion (POST)...")
        phone_id = options['phone_id'] or getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '') or '1520521787808608'
        simulated_sender = '+919876543210'
        simulated_text = 'Hello CRM Diagnostic Test Message'

        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "1839281717310154",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "918925893229",
                            "phone_number_id": phone_id
                        },
                        "contacts": [{
                            "profile": {"name": "CRM Diagnostic Lead"},
                            "wa_id": simulated_sender.replace('+', '')
                        }],
                        "messages": [{
                            "from": simulated_sender.replace('+', ''),
                            "id": f"wamid.DIAGNOSTIC_{os.urandom(6).hex()}",
                            "timestamp": "1732100000",
                            "text": {"body": simulated_text},
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }

        payload_bytes = json.dumps(payload).encode('utf-8')

        # Pick secret for signature
        active_secret = list(candidate_secrets)[0] if candidate_secrets else "50bb27751fdd0cfb887dd4db5e54dab8"
        signature_hash = hmac.new(active_secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()

        post_request = factory.post(
            '/webhook/whatsapp/',
            data=payload_bytes,
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256=f"sha256={signature_hash}"
        )

        try:
            post_response = WhatsAppWebhookView.as_view()(post_request)
            if post_response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("    PASS: Simulated message processed successfully (HTTP 200)."))

                # Verify in database
                from chat.models import Conversation, Message
                from leads.models import Lead

                conv = Conversation.objects.filter(phone_number=simulated_sender).first()
                if conv:
                    self.stdout.write(f"    - Conversation ID: {conv.id} | Phone: {conv.phone_number} | Last message: '{conv.last_message}'")
                else:
                    self.stdout.write(self.style.WARNING("    - Conversation was not found in database."))

                lead = Lead.objects.filter(phone__endswith=simulated_sender[-10:]).first()
                if lead:
                    self.stdout.write(f"    - Lead Created ID: {lead.id} | Name: '{lead.name}' | Source: '{lead.source}' | Status: '{lead.status}'")
                else:
                    self.stdout.write("    - Lead record: Existing lead matched or pending assignment.")
            else:
                self.stdout.write(self.style.ERROR(f"    FAIL: Webhook returned HTTP {post_response.status_code}: {post_response.content}"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"    EXCEPTION during webhook processing: {exc}"))

        self.stdout.write("\n==================================================")
        self.stdout.write(" DIAGNOSTIC COMPLETE")
        self.stdout.write("==================================================")
