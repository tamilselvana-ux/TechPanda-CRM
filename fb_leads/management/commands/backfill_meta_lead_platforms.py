import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.management.base import BaseCommand
from django.db import transaction

from fb_leads.facebook import _get, normalize_meta_platform
from fb_leads.models import FacebookLead
from leads.models import Lead

log = logging.getLogger("crm")


def fetch_lead_platform(fb_info):
    """Worker function to fetch lead info from Graph API in parallel with robust fallbacks."""
    lead_id, leadgen_id, page_id, ad_name, campaign_name, form_name, existing_platform, lead_platform = fb_info
    try:
        data = _get(
            leadgen_id,
            {"fields": "id,created_time,platform,ad_id,ad_name,campaign_name"},
            page_id=page_id,
        )
        raw_plat = data.get("platform")
        resolved = normalize_meta_platform(
            raw_plat,
            ad_name=data.get("ad_name") or ad_name,
            campaign_name=data.get("campaign_name") or campaign_name,
            form_name=form_name,
        )
        return (lead_id, resolved, True, "")
    except Exception as exc:
        if lead_platform in ("facebook", "instagram"):
            resolved = lead_platform
        else:
            resolved = normalize_meta_platform(
                "",
                ad_name=ad_name,
                campaign_name=campaign_name,
                form_name=form_name,
            )
            if resolved == "unknown" and existing_platform in ("facebook", "instagram"):
                resolved = existing_platform
            elif resolved == "unknown":
                resolved = "facebook"

        return (lead_id, resolved, False, str(exc))


class Command(BaseCommand):
    help = (
        "Backfill platform (facebook / instagram / unknown) for existing Meta leads "
        "by re-fetching from Meta Graph API, with fallback to metadata heuristics."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate backfill without persisting updates to database.",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=15,
            help="Number of concurrent worker threads (default: 15).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        max_workers = options["workers"]

        leads_data = list(
            FacebookLead.objects.values_list(
                "id", "leadgen_id", "page_id", "ad_name", "campaign_name", "form_name", "platform", "lead__platform"
            ).order_by("id")
        )
        total_leads = len(leads_data)

        self.stdout.write(f"Starting Meta Leads Platform backfill for {total_leads} leads using {max_workers} worker threads...")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN mode enabled: No database changes will be saved."))

        counts = {
            "facebook": 0,
            "instagram": 0,
            "unknown": 0,
        }
        api_successes = 0
        api_failures = 0
        failure_details = []
        results = []

        completed_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(fetch_lead_platform, item) for item in leads_data]
            for future in as_completed(futures):
                lead_id, resolved_platform, is_success, err_msg = future.result()
                results.append((lead_id, resolved_platform))
                counts[resolved_platform] = counts.get(resolved_platform, 0) + 1
                if is_success:
                    api_successes += 1
                else:
                    api_failures += 1
                    if len(failure_details) < 5:
                        failure_details.append(f"Lead ID {lead_id}: {err_msg}")

                completed_count += 1
                if completed_count % 50 == 0 or completed_count == total_leads:
                    self.stdout.write(f"Processed {completed_count}/{total_leads} leads...")

        if not dry_run:
            self.stdout.write("Persisting backfill updates to database...")
            platform_map = dict(results)
            all_fb_leads = FacebookLead.objects.filter(id__in=platform_map.keys()).select_related("lead")
            
            leads_to_update = []
            crm_leads_to_update = []

            for fb in all_fb_leads:
                new_plat = platform_map.get(fb.id, "unknown")
                if fb.platform != new_plat:
                    fb.platform = new_plat
                    leads_to_update.append(fb)

                if fb.lead_id and fb.lead:
                    crm_lead = fb.lead
                    changed = False
                    if crm_lead.platform != new_plat:
                        crm_lead.platform = new_plat
                        changed = True
                    if crm_lead.source != "Meta":
                        crm_lead.source = "Meta"
                        changed = True
                    if changed:
                        crm_leads_to_update.append(crm_lead)

            if leads_to_update:
                FacebookLead.objects.bulk_update(leads_to_update, ["platform"], batch_size=200)
            if crm_leads_to_update:
                Lead.objects.bulk_update(crm_leads_to_update, ["platform", "source"], batch_size=200)

        self.stdout.write("\n" + "=" * 55)
        self.stdout.write(self.style.SUCCESS("Meta Leads Platform Backfill Complete"))
        self.stdout.write("=" * 55)
        self.stdout.write(f"Total Meta Leads Examined:  {total_leads}")
        self.stdout.write(f"Graph API Fetches Succeeded: {api_successes}")
        self.stdout.write(f"Graph API Fetches Failed:    {api_failures} (used metadata fallback)")
        self.stdout.write("\nBreakdown by Platform:")
        self.stdout.write(f"  - Facebook:  {counts.get('facebook', 0)}")
        self.stdout.write(f"  - Instagram: {counts.get('instagram', 0)}")
        self.stdout.write(f"  - Unknown:   {counts.get('unknown', 0)}")
        if failure_details:
            self.stdout.write("\nSample Graph API Failures:")
            for detail in failure_details:
                self.stdout.write(f"  * {detail}")
        self.stdout.write("=" * 55 + "\n")
