import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from telecrm_sync.client import TeleCRMAuthError, TeleCRMClient, TeleCRMError
from telecrm_sync.mapper import (
    DEFAULT_STATUS_MAP,
    ingest_lead_actions,
    ingest_or_merge_lead,
    ms_to_datetime,
    normalize_telecrm_phone,
    resolve_crm_status,
    suppress_sync_side_effects,
)
from telecrm_sync.models import (
    TeleCRMAction,
    TeleCRMLead,
    TeleCRMStatusMap,
    TeleCRMSyncRun,
    TeleCRMUser,
)

logger = logging.getLogger("telecrm_sync")
User = get_user_model()


class Command(BaseCommand):
    help = "One-time historical import command from TeleCRM into TechPanda CRM"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max",
            type=int,
            default=None,
            help="Maximum number of leads to import (e.g. --max 200 for dry testing)"
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=getattr(settings, "TELECRM_MAX_WORKERS", 5),
            help="Number of concurrent worker threads for history retrieval (default: 5)"
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Database transaction batch size for mapping (default: 500)"
        )
        parser.add_argument(
            "--resume",
            action="store_true",
            help="Resume from the last uncompleted import run"
        )
        parser.add_argument(
            "--skip-history",
            action="store_true",
            help="Skip fetching timeline actions history (leads only)"
        )
        parser.add_argument(
            "--token",
            type=str,
            default=None,
            help="Override TELECRM_TOKEN"
        )
        parser.add_argument(
            "--enterprise-id",
            type=str,
            default=None,
            help="Override TELECRM_ENTERPRISE_ID"
        )

    def handle(self, *args, **options):
        max_limit: Optional[int] = options["max"]
        workers: int = max(1, options["workers"])
        batch_size: int = max(1, options["batch_size"])
        resume_flag: bool = options["resume"]
        skip_history: bool = options["skip_history"]
        token: Optional[str] = options["token"]
        enterprise_id: Optional[str] = options["enterprise_id"]

        self.stdout.write("================================================================================")
        self.stdout.write("TechPanda CRM: TeleCRM Historical One-Time Import")
        self.stdout.write("================================================================================")

        client = TeleCRMClient(token=token, enterprise_id=enterprise_id)
        if not client.token:
            raise CommandError("TELECRM_TOKEN is not configured in settings or environment. Pass via --token.")

        # 1. Concurrency and run tracking
        sync_run = self._initialize_sync_run(resume_flag)
        self.stdout.write(f"Sync Run ID: {sync_run.id} | Mode: {sync_run.kind} | Status: {sync_run.status}")

        start_time = time.time()

        try:
            # 2. Step 0: Sync team members and lead-stage pipeline metadata
            self.stdout.write("\n[Step 0/3] Synchronizing Team Members and Status Pipeline Metadata...")
            self._sync_metadata(client, sync_run)

            # 3. Step A: List and mirror leads
            self.stdout.write("\n[Step 1/3] Extracting Leads from TeleCRM...")
            self._import_leads(client, sync_run, max_limit)

            # 4. Step B: Fetch action history
            if not skip_history:
                self.stdout.write("\n[Step 2/3] Fetching Action History via ThreadPoolExecutor...")
                self._import_action_history(client, sync_run, workers, max_limit)
            else:
                self.stdout.write("\n[Step 2/3] Action history extraction skipped via --skip-history.")

            # 5. Step C: Map into native CRM models
            self.stdout.write("\n[Step 3/3] Mapping Leads and Actions into Native CRM Database...")
            self._map_records_to_crm(sync_run, batch_size, max_limit)

            # Complete run
            sync_run.status = "COMPLETED"
            sync_run.finished_at = timezone.now()
            sync_run.save(update_fields=["status", "finished_at", "cursor", "leads_seen", "leads_created", "leads_merged", "actions_created", "errors"])

            elapsed = time.time() - start_time
            self._print_summary(sync_run, elapsed)

        except TeleCRMAuthError as auth_err:
            sync_run.status = "FAILED"
            sync_run.finished_at = timezone.now()
            sync_run.errors.append({"error": "AuthError", "detail": str(auth_err), "timestamp": timezone.now().isoformat()})
            sync_run.save(update_fields=["status", "finished_at", "errors"])
            raise CommandError(f"Authentication failed: {auth_err}") from auth_err

        except Exception as exc:
            sync_run.status = "FAILED"
            sync_run.finished_at = timezone.now()
            sync_run.errors.append({"error": "UnhandledException", "detail": str(exc), "timestamp": timezone.now().isoformat()})
            sync_run.save(update_fields=["status", "finished_at", "errors"])
            logger.exception("Import run %s encountered fatal error: %s", sync_run.id, exc)
            raise CommandError(f"Import process failed: {exc}") from exc

    def _initialize_sync_run(self, resume_flag: bool) -> TeleCRMSyncRun:
        """Initializes or resumes a database-backed TeleCRMSyncRun."""
        if resume_flag:
            existing = TeleCRMSyncRun.objects.filter(kind="import", status="RUNNING").order_by("-started_at").first()
            if existing:
                self.stdout.write(f"Resuming existing import run #{existing.id} started at {existing.started_at}")
                return existing

        # Check for uncompleted runs in last 2 hours
        cutoff = timezone.now() - timezone.timedelta(hours=2)
        active_run = TeleCRMSyncRun.objects.filter(kind="import", status="RUNNING", started_at__gte=cutoff).first()
        if active_run:
            self.stdout.write(
                f"Warning: An active import run (#{active_run.id}) was started at {active_run.started_at}. "
                "Use --resume to continue it, or mark it FAILED in admin."
            )

        return TeleCRMSyncRun.objects.create(
            kind="import",
            status="RUNNING",
            started_at=timezone.now(),
            cursor={"skip": 0, "history_done": False, "mapping_done": False}
        )

    def _sync_metadata(self, client: TeleCRMClient, sync_run: TeleCRMSyncRun):
        """Fetches team members and lead-stage pipeline metadata from TeleCRM."""
        # 1. Team Members
        try:
            members = client.get_team_members()
            self.stdout.write(f"  Retrieved {len(members)} team member records.")
            for m in members:
                uid = str(m.get("uid") or m.get("id") or m.get("userId") or "").strip()
                email = str(m.get("email") or "").strip().lower()
                name = str(m.get("name") or "").strip()
                if not uid:
                    continue

                crm_u = None
                if email:
                    crm_u = User.objects.filter(email__iexact=email).first()

                TeleCRMUser.objects.update_or_create(
                    uid=uid,
                    defaults={
                        "email": email,
                        "name": name,
                        "crm_user": crm_u
                    }
                )
        except Exception as exc:
            self.stdout.write(f"  Notice: Team members endpoint returned: {exc}")

        # 2. Lead Stage Pipeline
        try:
            pipeline = client.get_lead_stage_pipeline()
            statuses = pipeline.get("statuses") or []
            self.stdout.write(f"  Retrieved {len(statuses)} pipeline status definitions.")
            for st in statuses:
                s_id = str(st.get("id") or "").strip()
                label = str(st.get("label") or st.get("name") or "").strip()
                if not label:
                    continue
                crm_st = resolve_crm_status(label, s_id)
                TeleCRMStatusMap.objects.update_or_create(
                    telecrm_status_name=label,
                    defaults={
                        "telecrm_status_id": s_id,
                        "crm_status": crm_st
                    }
                )
        except Exception as exc:
            self.stdout.write(f"  Notice: Pipeline metadata endpoint returned: {exc}")

    def _import_leads(self, client: TeleCRMClient, sync_run: TeleCRMSyncRun, max_limit: Optional[int]):
        """Paginates TeleCRM /lead/search and stores raw lead mirrors."""
        total_enterprise_leads = client.count_leads()
        self.stdout.write(f"  Total leads reported in TeleCRM enterprise: {total_enterprise_leads}")

        target_count = min(total_enterprise_leads, max_limit) if max_limit else total_enterprise_leads
        current_skip = sync_run.cursor.get("skip", 0)

        batch_leads_to_create = []
        page_size = 100

        while current_skip < target_count:
            fetch_limit = min(page_size, target_count - current_skip)
            leads_page = client.list_leads(skip=current_skip, limit=fetch_limit)
            if not leads_page:
                self.stdout.write(f"  Reached end of leads at skip={current_skip}.")
                break

            for raw_lead in leads_page:
                tc_id = str(raw_lead.get("id") or "").strip()
                if not tc_id:
                    continue

                fields = raw_lead.get("fields") or {}
                raw_phone = fields.get("phone")
                clean_phone = normalize_telecrm_phone(raw_phone, tc_id)
                c_ms = fields.get("created_on") or raw_lead.get("creationTimestamp")
                m_ms = fields.get("modified_on")
                c_dt = ms_to_datetime(c_ms)
                m_dt = ms_to_datetime(m_ms)

                TeleCRMLead.objects.update_or_create(
                    telecrm_id=tc_id,
                    defaults={
                        "phone": clean_phone,
                        "raw": raw_lead,
                        "telecrm_created_at": c_dt,
                        "telecrm_modified_at": m_dt,
                    }
                )
                sync_run.leads_seen += 1

            current_skip += len(leads_page)
            sync_run.cursor["skip"] = current_skip
            sync_run.save(update_fields=["leads_seen", "cursor"])

            pct = (current_skip / target_count) * 100 if target_count else 100
            self.stdout.write(f"  Leads Extracted: {current_skip}/{target_count} ({pct:.1f}%)")

            if len(leads_page) < fetch_limit:
                break

    def _import_action_history(
        self,
        client: TeleCRMClient,
        sync_run: TeleCRMSyncRun,
        workers: int,
        max_limit: Optional[int]
    ):
        """Fetches history for TeleCRMLead records using a thread pool."""
        qs = TeleCRMLead.objects.filter(history_fetched=False).order_by("-telecrm_created_at")
        if max_limit:
            qs = qs[:max_limit]

        lead_ids = list(qs.values_list("telecrm_id", flat=True))
        total_leads = len(lead_ids)
        if total_leads == 0:
            self.stdout.write("  All targeted leads already have history fetched.")
            return

        self.stdout.write(f"  Fetching history for {total_leads} leads across {workers} worker threads...")

        completed = 0
        total_actions_created = 0

        def fetch_actions_for_lead(lead_id: str) -> Tuple[str, List[Dict[str, Any]]]:
            actions = []
            skip = 0
            while True:
                page, total = client.get_lead_actions(lead_id, skip=skip, limit=100)
                if not page:
                    break
                actions.extend(page)
                skip += len(page)
                if skip >= total or len(page) < 100:
                    break
            return lead_id, actions

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_lead = {
                executor.submit(fetch_actions_for_lead, lid): lid for lid in lead_ids
            }

            for future in as_completed(future_to_lead):
                completed += 1
                lead_id = future_to_lead[future]
                try:
                    _, actions = future.result()
                    tc_lead = TeleCRMLead.objects.filter(telecrm_id=lead_id).first()
                    if tc_lead and actions:
                        for act in actions:
                            act_id = str(act.get("id") or "").strip()
                            if not act_id:
                                continue
                            a_type = str(act.get("type") or "UNKNOWN").upper()
                            occ_dt = ms_to_datetime(act.get("creationTimestamp")) or timezone.now()
                            emp_uid = str(act.get("employeeid") or "")

                            TeleCRMAction.objects.get_or_create(
                                telecrm_id=act_id,
                                defaults={
                                    "lead": tc_lead,
                                    "type": a_type,
                                    "occurred_at": occ_dt,
                                    "employee_uid": emp_uid,
                                    "raw": act
                                }
                            )
                            total_actions_created += 1

                    if tc_lead:
                        tc_lead.history_fetched = True
                        tc_lead.save(update_fields=["history_fetched"])

                except Exception as exc:
                    logger.warning("Error fetching actions for lead %s: %s", lead_id, exc)

                if completed % 100 == 0 or completed == total_leads:
                    pct = (completed / total_leads) * 100
                    sync_run.actions_created += total_actions_created
                    total_actions_created = 0
                    sync_run.save(update_fields=["actions_created"])
                    self.stdout.write(f"  History Progress: {completed}/{total_leads} leads ({pct:.1f}%)")

        sync_run.cursor["history_done"] = True
        sync_run.save(update_fields=["cursor", "actions_created"])

    def _map_records_to_crm(self, sync_run: TeleCRMSyncRun, batch_size: int, max_limit: Optional[int]):
        """Runs the deterministic mapper in atomic batches under side-effect suppression."""
        qs = TeleCRMLead.objects.all().order_by("-telecrm_created_at")
        if max_limit:
            qs = qs[:max_limit]

        total_to_map = qs.count()
        self.stdout.write(f"  Mapping {total_to_map} TeleCRM leads into CRM native tables (batch size: {batch_size})...")

        user_cache: Dict[str, Optional[User]] = {}
        processed = 0

        with suppress_sync_side_effects():
            for i in range(0, total_to_map, batch_size):
                batch_qs = qs[i:i + batch_size]
                batch_leads = list(batch_qs)

                with transaction.atomic():
                    # Pre-fetch actions for this batch to minimize queries
                    batch_tc_ids = [l.id for l in batch_leads]
                    actions_by_lead_id: Dict[int, List[Dict[str, Any]]] = {}
                    for act in TeleCRMAction.objects.filter(lead_id__in=batch_tc_ids).order_by("occurred_at"):
                        if act.lead_id not in actions_by_lead_id:
                            actions_by_lead_id[act.lead_id] = []
                        actions_by_lead_id[act.lead_id].append(act.raw)

                    for tc_lead in batch_leads:
                        try:
                            lead_actions = actions_by_lead_id.get(tc_lead.id, [])
                            lead, tc_mirror, was_created = ingest_or_merge_lead(
                                raw_lead=tc_lead.raw,
                                actions=lead_actions,
                                user_cache=user_cache
                            )

                            if was_created:
                                sync_run.leads_created += 1
                            else:
                                sync_run.leads_merged += 1

                            if lead_actions:
                                mapped_actions = ingest_lead_actions(
                                    lead=lead,
                                    tc_lead=tc_mirror,
                                    raw_actions=lead_actions,
                                    user_cache=user_cache
                                )

                        except Exception as exc:
                            logger.exception("Error mapping lead %s: %s", tc_lead.telecrm_id, exc)
                            sync_run.errors.append({
                                "telecrm_id": tc_lead.telecrm_id,
                                "error": str(exc),
                                "timestamp": timezone.now().isoformat()
                            })

                processed += len(batch_leads)
                sync_run.save(update_fields=["leads_created", "leads_merged", "errors"])
                pct = (processed / total_to_map) * 100 if total_to_map else 100
                self.stdout.write(f"  Mapping Progress: {processed}/{total_to_map} ({pct:.1f}%) | Created: {sync_run.leads_created} | Merged: {sync_run.leads_merged}")

    def _print_summary(self, sync_run: TeleCRMSyncRun, elapsed_sec: float):
        """Prints a clean, structured completion summary."""
        self.stdout.write("\n================================================================================")
        self.stdout.write("TeleCRM Import Completed Successfully")
        self.stdout.write("================================================================================")
        self.stdout.write(f"Run ID:                  {sync_run.id}")
        self.stdout.write(f"Status:                  {sync_run.status}")
        self.stdout.write(f"Elapsed Time:            {elapsed_sec:.2f} seconds")
        self.stdout.write(f"Total Leads Seen:        {sync_run.leads_seen}")
        self.stdout.write(f"New Leads Created:       {sync_run.leads_created}")
        self.stdout.write(f"Existing Leads Merged:   {sync_run.leads_merged}")
        self.stdout.write(f"Actions Mapped:          {sync_run.actions_created}")
        self.stdout.write(f"Errors Logged:           {len(sync_run.errors)}")
        self.stdout.write("================================================================================")
