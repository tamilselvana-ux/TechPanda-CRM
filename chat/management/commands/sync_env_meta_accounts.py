from django.core.management.base import BaseCommand
from services.env_meta_sync import sync_all_env_meta_accounts


class Command(BaseCommand):
    help = "Synchronizes all WhatsApp Business Lines and Facebook Pages declared in .env into the CRM database."

    def handle(self, *args, **options):
        self.stdout.write("Scanning .env for WhatsApp and Facebook multi-developer account configurations...")
        stats = sync_all_env_meta_accounts(stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS(
            f"Successfully synced Meta accounts from .env:\n"
            f"  - WhatsApp accounts created: {stats['whatsapp_created']}, updated: {stats['whatsapp_updated']}\n"
            f"  - Facebook pages created: {stats['facebook_created']}, updated: {stats['facebook_updated']}"
        ))
