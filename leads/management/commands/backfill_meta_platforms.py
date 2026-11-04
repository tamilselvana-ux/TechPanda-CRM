import logging
import re
from django.core.management.base import BaseCommand
from django.apps import apps
from leads.models import Lead

log = logging.getLogger('crm')
IG_REGEX = re.compile(r'\b(ig|insta|instagram)\b', re.IGNORECASE)


class Command(BaseCommand):
    help = "Backfill platform and separate Facebook vs Instagram leads across historical CRM data."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help="Scan and report without saving changes")

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        self.stdout.write(self.style.NOTICE(f"Starting Meta Leads Platform Backfill (dry_run={dry_run})..."))

        Channel = apps.get_model('channels', 'Channel')
        fb_channel = Channel.objects.filter(name__iexact='Facebook').first()
        ig_channel = Channel.objects.filter(name__iexact='Instagram').first()

        total_scanned = 0
        fb_assigned = 0
        ig_assigned = 0
        wa_assigned = 0
        direct_assigned = 0
        google_assigned = 0
        other_assigned = 0

        qs = Lead.objects.all().select_related('channel').prefetch_related('facebook_entries')
        
        for lead in qs:
            total_scanned += 1
            changed = False
            src = (lead.source or '').strip()
            chan_name = (getattr(lead.channel, 'name', '') or '').strip()
            notes = (lead.notes or '').lower()

            # Check Facebook entries
            fb_entries = list(lead.facebook_entries.all())
            is_instagram = False

            if fb_entries:
                for entry in fb_entries:
                    text_corpus = f"{entry.campaign_name or ''} {entry.ad_name or ''} {entry.form_name or ''} {entry.all_answers}"
                    if (getattr(entry, 'platform', '') or '').lower() in ['ig', 'instagram']:
                        is_instagram = True
                        break
                    if IG_REGEX.search(text_corpus):
                        is_instagram = True
                        break
            
            # Check notes or username for clear Instagram signals
            if not is_instagram:
                if IG_REGEX.search(notes):
                    is_instagram = True
                elif any(lead.name.startswith(p) for p in ['@', '__']) and (' ' not in lead.name.strip()):
                    is_instagram = True

            if is_instagram or src == 'Instagram' or chan_name == 'Instagram':
                if lead.source != 'Instagram':
                    lead.source = 'Instagram'
                    changed = True
                if lead.platform != 'instagram':
                    lead.platform = 'instagram'
                    changed = True
                if ig_channel and lead.channel_id != ig_channel.id:
                    lead.channel = ig_channel
                    changed = True
                ig_assigned += 1

            elif src == 'Facebook' or chan_name == 'Facebook' or fb_entries:
                if lead.platform != 'facebook':
                    lead.platform = 'facebook'
                    changed = True
                if fb_channel and lead.channel_id != fb_channel.id:
                    lead.channel = fb_channel
                    changed = True
                fb_assigned += 1

            elif src == 'WhatsApp' or chan_name == 'WhatsApp':
                if lead.platform != 'whatsapp':
                    lead.platform = 'whatsapp'
                    changed = True
                wa_assigned += 1

            elif src == 'Walk-in' or chan_name == 'Walk-in':
                if lead.platform != 'direct':
                    lead.platform = 'direct'
                    changed = True
                direct_assigned += 1

            elif 'google' in src.lower() or 'google' in chan_name.lower():
                if lead.platform != 'google':
                    lead.platform = 'google'
                    changed = True
                google_assigned += 1

            else:
                if lead.platform != 'other':
                    lead.platform = 'other'
                    changed = True
                other_assigned += 1

            if changed and not dry_run:
                lead.save(update_fields=['source', 'platform', 'channel'])

        self.stdout.write(self.style.SUCCESS(
            f"Backfill Complete!\n"
            f"Total Leads Processed: {total_scanned}\n"
            f"  - Instagram: {ig_assigned}\n"
            f"  - Facebook: {fb_assigned}\n"
            f"  - WhatsApp: {wa_assigned}\n"
            f"  - Walk-in / Direct: {direct_assigned}\n"
            f"  - Google: {google_assigned}\n"
            f"  - Other: {other_assigned}"
        ))
