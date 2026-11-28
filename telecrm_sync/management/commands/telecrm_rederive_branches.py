from collections import Counter
from django.core.management.base import BaseCommand
from django.db.models import Q
from telecrm_sync.mapper import resolve_branch_from_text, resolve_telecrm_user
from telecrm_sync.models import TeleCRMLead


class Command(BaseCommand):
    help = "Re-derives branch and branch_source for TeleCRM-linked leads with branch_source='none' (old T. Nagar default or blank)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Compute changes without writing to DB")

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        qs = (
            TeleCRMLead.objects
            .filter(crm_lead__isnull=False, crm_lead__branch_source="none")
            .filter(Q(crm_lead__branch__isnull=True) | Q(crm_lead__branch__name="T. Nagar"))
            .select_related(
                "crm_lead",
                "crm_lead__branch",
                "crm_lead__assigned_telecaller__branch",
                "crm_lead__assigned_counselor__branch",
                "crm_lead__assigned_branch_head__branch",
                "crm_lead__assigned_sales_head__branch",
            )
        )
        total = qs.count()
        changed_branch = 0
        kept_same = 0
        before_counts = Counter()
        source_counts = Counter()
        branch_counts = Counter()
        sample_changes = []
        user_cache = {}

        for tl in qs:
            lead = tl.crm_lead
            before_counts[lead.branch.name if lead.branch else "Unknown"] += 1

            raw = tl.raw or {}
            fields = raw.get("fields") or {}
            raw_status_label = str(fields.get("status") or raw.get("status") or "").strip().lower()

            status_branch = None
            if raw_status_label.startswith("won_"):
                status_branch = resolve_branch_from_text(raw_status_label[4:].strip())
            elif "center visited _" in raw_status_label or "centre visited _" in raw_status_label:
                status_branch = resolve_branch_from_text(raw_status_label.split("_")[-1].strip())

            pref_branch = resolve_branch_from_text(fields.get("preferred_branch")) if fields.get("preferred_branch") else None
            base_branch = resolve_branch_from_text(fields.get("base_branch")) if fields.get("base_branch") else None

            assigned_user = (
                resolve_telecrm_user(raw.get("employeeid"), user_cache)
                or lead.assigned_telecaller
                or lead.assigned_counselor
                or lead.assigned_branch_head
                or lead.assigned_sales_head
            )
            assignee_branch = getattr(assigned_user, "branch", None) if assigned_user else None

            if status_branch:
                new_branch, new_src = status_branch, "status"
            elif pref_branch:
                new_branch, new_src = pref_branch, "preferred"
            elif base_branch:
                new_branch, new_src = base_branch, "base"
            elif assignee_branch:
                new_branch, new_src = assignee_branch, "assignee"
            else:
                new_branch, new_src = None, "none"

            old_branch_id = lead.branch_id
            new_branch_id = new_branch.id if new_branch else None
            old_name = lead.branch.name if lead.branch else "Unknown"
            new_name = new_branch.name if new_branch else "Unknown"
            if old_branch_id != new_branch_id:
                changed_branch += 1
                if len(sample_changes) < 10:
                    sample_changes.append((lead.id, old_name, new_name, new_src))
            else:
                kept_same += 1

            source_counts[new_src] += 1
            branch_counts[new_name] += 1

            if not dry_run and (old_branch_id != new_branch_id or lead.branch_source != new_src):
                lead.branch = new_branch
                lead.branch_source = new_src
                lead.save(update_fields=["branch", "branch_source"])

        mode = "DRY RUN" if dry_run else "APPLIED"
        self.stdout.write(f"[{mode}] Scanned TeleCRM-linked leads with branch_source='none' (blank/T. Nagar default): {total}")
        self.stdout.write(f"  Branch changed: {changed_branch} | Branch unchanged: {kept_same}")
        self.stdout.write(f"  Before branch distribution: {dict(before_counts)}")
        self.stdout.write(f"  New branch_source counts:   {dict(source_counts)}")
        self.stdout.write(f"  New branch distribution:    {dict(branch_counts)}")
        if sample_changes:
            self.stdout.write("  Sample changes (up to 10):")
            for lid, old_n, new_n, src in sample_changes:
                self.stdout.write(f"    Lead #{lid}: {old_n} -> {new_n} (source={src})")
