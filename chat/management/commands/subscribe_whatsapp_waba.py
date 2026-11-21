import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from chat.models import BusinessAccount


class Command(BaseCommand):
    help = "Checks and subscribes WhatsApp Business Account (WABA) to the App webhooks via Graph API."

    def add_arguments(self, parser):
        parser.add_argument('--waba-id', type=str, default=None, help='WhatsApp Business Account ID')
        parser.add_argument('--token', type=str, default=None, help='Meta Access Token')

    def handle(self, *args, **options):
        self.stdout.write("==================================================")
        self.stdout.write(" WHATSAPP WABA WEBHOOK SUBSCRIPTION CHECK")
        self.stdout.write("==================================================\n")

        # Resolve credentials
        token = options['token'] or os.getenv('WHATSAPP_ACCESS_TOKEN') or getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
        waba_id = options['waba_id'] or os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID') or getattr(settings, 'WHATSAPP_BUSINESS_ACCOUNT_ID', '')

        # Check BusinessAccount in DB if not in settings
        if not waba_id:
            biz = BusinessAccount.objects.filter(is_active=True).first()
            if biz and getattr(biz, 'business_account_id', None):
                waba_id = biz.business_account_id
                if not token and getattr(biz, 'access_token', None):
                    token = biz.access_token

        if not token:
            self.stdout.write(self.style.ERROR("FAIL: No WHATSAPP_ACCESS_TOKEN found in environment, settings, or database."))
            return

        if not waba_id:
            self.stdout.write(self.style.ERROR("FAIL: No WHATSAPP_BUSINESS_ACCOUNT_ID found in environment, settings, or database."))
            self.stdout.write("Provide it with --waba-id <ID> or set WHATSAPP_BUSINESS_ACCOUNT_ID in .env")
            return

        api_version = os.getenv('WHATSAPP_API_VERSION') or getattr(settings, 'WHATSAPP_API_VERSION', 'v21.0')
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Step 1: Check existing subscribed apps
        self.stdout.write(f"Checking current webhook subscriptions for WABA: {waba_id}...")
        url = f"https://graph.facebook.com/{api_version}/{waba_id}/subscribed_apps"

        try:
            get_res = requests.get(url, headers=headers, timeout=15)
            self.stdout.write(f"GET /subscribed_apps status: {get_res.status_code}")
            get_data = get_res.json()
            self.stdout.write(f"Current subscriptions response: {get_data}")

            is_subscribed = False
            if get_res.status_code == 200 and "data" in get_data and len(get_data["data"]) > 0:
                is_subscribed = True
                self.stdout.write(self.style.SUCCESS("PASS: WABA is already subscribed to an App!"))

            # Step 2: Subscribe (or re-subscribe) WABA to this App
            self.stdout.write("\nSubscribing WABA to App webhooks now (POST /subscribed_apps)...")
            post_res = requests.post(url, headers=headers, timeout=15)
            self.stdout.write(f"POST /subscribed_apps status: {post_res.status_code}")
            post_data = post_res.json()
            self.stdout.write(f"Subscription result: {post_data}")

            if post_res.status_code == 200 and post_data.get("success") is True:
                self.stdout.write(self.style.SUCCESS("\nSUCCESS! WABA is now successfully subscribed to your App webhooks."))
                self.stdout.write("Meta will now dispatch all incoming user messages to your Callback URL.")
            else:
                self.stdout.write(self.style.ERROR(f"\nFAILED to subscribe WABA: {post_data}"))

        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Error communicating with Graph API: {exc}"))
