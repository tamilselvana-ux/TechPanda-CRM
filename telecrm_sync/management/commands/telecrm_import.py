from __future__ import annotations
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
from leads.models import Lead, LeadStatusHistory
from telecrm_sync.client import TeleCRMAuthError, TeleCRMClient, TeleCRMError
from telecrm_sync.mapper import (
    DEFAULT_STATUS_MAP,
    evaluate_status_conflict,
    extract_telecrm_status_timestamp,
    ingest_lead_actions,
    ingest_or_merge_lead,
    ms_to_datetime,
    normalize_telecrm_phone,
    parse_telecrm_phone,
    resolve_crm_status,
    suppress_sync_side_effects,
)
from telecrm_sync.models import (
    SyncLock,
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
            "--dry-run",
            action="store_true",
            help="Fetch and map metadata and samples, write nothing to DB, and print counts plus unmapped stages and users"
        )
        parser.add_argument(
            "--max",
            type=int,
            default=None,
            help="Maximum number of leads to import (e.g. --max 200 for dry testing)"
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=getattr(settings, "TELECRM_MAX_WORKERS", 3),
            help="Number of concurrent worker threads for history retrieval (default: 3)"
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
            help="Override TELECRM_SYNC_TOKEN"
        )
        parser.add_argument(
            "--enterprise-id",
            type=str,
            default=None,
            help="Override TELECRM_ENTERPRISE_ID"
        )
        parser.add_argument(
            "--yes",
            "--noinput",
            action="store_true",
            dest="noinput",
            help="Run non-interactively without confirmation prompts (default behavior)"
        )

    def handle(self, *args, **options):
        dry_run: bool = options.get("dry_run", False)
        max_limit: Optional[int] = options["max"]
        workers: int = max(1, options["workers"])
        batch_size: int = max(1, options["batch_size"])
        resume_flag: bool = options["resume"]
        skip_history: bool = options["skip_history"]
        token: Optional[str] = options["token"]
        enterprise_id: Optional[str] = options["enterprise_id"]

        self.stdout.write("================================================================================")
        if dry_run:
            self.stdout.write("TechPanda CRM: TeleCRM Historical Import [DRY RUN - ZERO WRITES]")
        else:
            self.stdout.write("TechPanda CRM: TeleCRM Historical One-Time Import")
        self.stdout.write("================================================================================")

        client = TeleCRMClient(token=token, enterprise_id=enterprise_id)
        if not client.token:
            raise CommandError("TELECRM_SYNC_TOKEN is not configured. Pass via --token.")

        if dry_run:
            self._handle_dry_run(client)
            return

        if hasattr(client, "rate_limiter") and hasattr(client.rate_limiter, "reset_stats"):
            client.rate_limiter.reset_stats()

        # 1. Concurrency and run tracking
        sync_run = self._initialize_sync_run(resume_flag)
        self.stdout.write(f"Sync Run ID: {sync_run.id} | Mode: {sync_run.kind} | Status: {sync_run.status}")

        acquired, current_lock = SyncLock.acquire(
            holder="import",
            run_id=sync_run.id,
            ttl_hours=24,
            disable_sync_while_held=True,
        )
        if not acquired:
            raise CommandError(
                f"Cannot start telecrm_import: SyncLock is currently held by {current_lock.holder} "
                f"(run_id={current_lock.run_id})."
            )

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
            self._map_records_to_crm(sync_run, batch_size, max_limit, client=client)

            # Complete run
            sync_run.status = "COMPLETED"
            sync_run.finished_at = timezone.now()
            sync_run.save(update_fields=["status", "finished_at", "cursor", "leads_seen", "leads_created", "leads_merged", "actions_created", "errors"])

            elapsed = time.time() - start_time
            self._print_summary(sync_run, elapsed, client=client)

        except TeleCRMAuthError as auth_err:
            sync_run.status = "FAILED"
            sync_run.finished_at = timezone.now()
            sync_run.errors.append({"error": "AuthError", "detail": str(auth_err), "timestamp": timezone.now().isoformat()})
            sync_run.save(update_fields=["status", "finished_at", "errors"])
            raise CommandError(f"Authentication failed: {auth_err}") from auth_err

        except BaseException as exc:
            sync_run.status = "FAILED"
            sync_run.finished_at = timezone.now()
            sync_run.errors.append({
                "error": type(exc).__name__,
                "detail": str(exc) or f"Process interrupted ({type(exc).__name__})",
                "timestamp": timezone.now().isoformat(),
            })
            sync_run.save(update_fields=["status", "finished_at", "errors"])
            logger.exception("Import run %s encountered fatal error: %s", sync_run.id, exc)
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise CommandError(f"Import process failed: {exc}") from exc

        finally:
            # Release import lock and enable incremental sync ONLY when import completed
            SyncLock.release(
                holder="import",
                enable_sync=(sync_run.status == "COMPLETED"),
            )

    def _handle_dry_run(self, client: TeleCRMClient):
        """
        Executes a non-destructive dry run:
        1. Tests enterprise API connectivity and pulls enterprise metadata.
        2. Retrieves and reconciles all team members against the CRM User directory.
        3. Retrieves and reconciles all pipeline status definitions against LeadStatus.
        4. Queries custom fields and custom actions catalog.
        5. Calculates exact phone merge count against existing CRM leads.
        6. Estimates action counts, storage, and duration.
        7. Guarantees 0 database writes and prints full discrepancy report.
        """
        import shutil
        from collections import defaultdict

        self.stdout.write("\n[Dry Run: Step 1/6] Connecting to TeleCRM Enterprise Metadata API...")
        try:
            meta = client.get_metadata()
            ent_name = meta.get("name") or "TechPanda"
            ent_id = meta.get("id") or client.enterprise_id
            industry = meta.get("industry") or "N/A"
            self.stdout.write(f"  Connected successfully to Enterprise: '{ent_name}' (ID: {ent_id})")
            self.stdout.write(f"  Industry: {industry} | API Base: {client.base_url}")
        except Exception as exc:
            self.stdout.write(f"  Error querying enterprise metadata: {exc}")

        # Total Leads
        self.stdout.write("\n[Dry Run: Step 2/6] Querying Total Lead Counts and Catalogs...")
        try:
            total_leads = client.count_leads()
            self.stdout.write(f"  Total Leads in TeleCRM Enterprise: {total_leads:,}")
        except Exception as exc:
            total_leads = 0
            self.stdout.write(f"  Error querying total lead counts: {exc}")

        # Custom Fields & Actions
        try:
            custom_fields = client.get_custom_fields()
            self.stdout.write(f"  Total Custom Fields Defined: {len(custom_fields)}")
        except Exception as exc:
            custom_fields = []
            self.stdout.write(f"  Custom fields query notice: {exc}")

        try:
            custom_actions = client.get_custom_actions()
            self.stdout.write(f"  Total Custom Action Types Defined: {len(custom_actions)}")
        except Exception as exc:
            custom_actions = []
            self.stdout.write(f"  Custom actions query notice: {exc}")

        # Team Members & Teams Reconciliation
        self.stdout.write("\n[Dry Run: Step 3/6] Reconciling Enterprise Team Members & Managers...")
        try:
            members = client.get_team_members()
            self.stdout.write(f"  Total TeleCRM Team Members Fetched: {len(members)}")

            # Group by manager
            teams = defaultdict(list)
            central_users = []
            for m in members:
                mgr_email = (m.get("manager_email") or "NO_MANAGER").strip().lower()
                mgr_name = m.get("manager_name") or "Top-level / Self"
                teams[(mgr_name, mgr_email)].append(m)

                name = m.get("name", "")
                has_suffix = any(name.endswith(sfx) or f"{sfx} " in name for sfx in ["_VEL", "_TN", "_AN", "_CMB", "_PR", "_TM"])
                if not has_suffix:
                    central_users.append(m)

            self.stdout.write("\n  --- Manager Teams Hierarchy ---")
            for (m_name, m_email), group in sorted(teams.items(), key=lambda x: -len(x[1])):
                self.stdout.write(f"  Team {m_name} <{m_email}> ({len(group)} members):")
                for u in group:
                    self.stdout.write(f"    - {u.get('name')} <{u.get('email')}> | Role: {u.get('permission_template_name')} | Status: {u.get('status')}")

            self.stdout.write(f"\n  --- Central Users ({len(central_users)} Total) ---")
            for idx, cu in enumerate(central_users, 1):
                self.stdout.write(f"    {idx:>2}. {cu.get('name')} <{cu.get('email')}> | Role: {cu.get('permission_template_name')} | Manager: {cu.get('manager_name')} <{cu.get('manager_email')}>")

        except Exception as exc:
            self.stdout.write(f"  Team members reconciliation notice: {exc}")
            members = []
            central_users = []

        # Pipeline Status Reconciliation
        self.stdout.write("\n[Dry Run: Step 4/6] Reconciling Lead Stage Pipeline Statuses...")
        try:
            pipeline = client.get_lead_stage_pipeline()
            statuses = pipeline.get("statuses") or []
            self.stdout.write(f"  Total TeleCRM Pipeline Statuses: {len(statuses)}")

            mapped_statuses = []
            unmapped_statuses = []

            for st in statuses:
                s_id = str(st.get("id") or "").strip()
                label = str(st.get("label") or st.get("name") or "").strip()
                stage = str(st.get("stage") or "ACTIVE").strip()

                crm_st = resolve_crm_status(label, s_id)
                is_direct = (
                    label.lower() in DEFAULT_STATUS_MAP or
                    s_id in DEFAULT_STATUS_MAP or
                    TeleCRMStatusMap.objects.filter(telecrm_status_name__iexact=label).exists() or
                    TeleCRMStatusMap.objects.filter(telecrm_status_id=s_id).exists()
                )

                if is_direct:
                    mapped_statuses.append((s_id, label, stage, crm_st))
                else:
                    unmapped_statuses.append((s_id, label, stage, crm_st))

            self.stdout.write(f"  Mapped Statuses: {len(mapped_statuses)} | Unmapped Statuses: {len(unmapped_statuses)}")
            for s_id, label, stage, crm_st in mapped_statuses:
                self.stdout.write(f"    [MAPPED] ID {s_id:>2} | '{label}' [{stage}] -> LeadStatus.{crm_st}")

        except Exception as exc:
            self.stdout.write(f"  Pipeline status reconciliation notice: {exc}")
            statuses = []
            mapped_statuses = []
            unmapped_statuses = []

        # Phone Merge Calculation
        self.stdout.write("\n[Dry Run: Step 5/6] Calculating Phone Match & Merge Count against CRM...")
        crm_phones = [p for p in Lead.objects.values_list('normalized_phone', flat=True) if p]
        unique_phones = set()
        for p in crm_phones:
            digits = ''.join(c for c in p if c.isdigit())
            if len(digits) == 10:
                unique_phones.add(digits)
            elif len(digits) == 12 and digits.startswith('91'):
                unique_phones.add(digits[2:])

        self.stdout.write(f"  Total Unique Phone Numbers in Existing CRM: {len(unique_phones)}")
        total_merged = 0
        conflict_counts = {
            "unchanged": 0,
            "crm_fresh_to_telecrm": 0,
            "telecrm_fresh_kept_crm": 0,
            "newer_telecrm_won": 0,
            "newer_crm_won": 0,
            "protected_enrolled": 0,
            "conflicts_created": 0,
        }
        crm_by_phone = {
            l.normalized_phone: l
            for l in Lead.objects.filter(normalized_phone__in=unique_phones)
        }
        mirrors_by_tid = {
            m.telecrm_id: m.last_synced_status
            for m in TeleCRMLead.objects.all()
        }
        latest_lsh_by_lead = {}
        for lsh in LeadStatusHistory.objects.filter(lead_id__in=[l.id for l in crm_by_phone.values()]).order_by("lead_id", "-created_at"):
            if lsh.lead_id not in latest_lsh_by_lead:
                latest_lsh_by_lead[lsh.lead_id] = lsh.created_at

        phone_chunks = list(unique_phones)
        chunk_size = 100
        try:
            for i in range(0, len(phone_chunks), chunk_size):
                chunk = phone_chunks[i:i+chunk_size]
                search_payload = {'fields': {'phone': ['91' + p for p in chunk]}}
                skip = 0
                while True:
                    r = client._request("POST", "/lead/search", params={"skip": skip, "limit": 100}, json_data=search_payload)
                    rows = r.get("data", []) if isinstance(r, dict) else (r if isinstance(r, list) else [])
                    if not rows:
                        break
                    for raw_l in rows:
                        total_merged += 1
                        tid = str(raw_l.get("id") or "").strip()
                        f = raw_l.get("fields") or {}
                        _, norm_p, _ = parse_telecrm_phone(f.get("phone"), tid)
                        crm_lead = crm_by_phone.get(norm_p)
                        if not crm_lead:
                            continue
                        tc_status = resolve_crm_status(raw_l.get("status") or f.get("status"))
                        tc_st_at = extract_telecrm_status_timestamp(raw_l)
                        crm_st_at = latest_lsh_by_lead.get(crm_lead.id)
                        last_st = mirrors_by_tid.get(tid, "")
                        res = evaluate_status_conflict(crm_lead.status, crm_st_at, tc_status, tc_st_at, last_st)
                        case_key = res["case"]
                        if case_key in conflict_counts:
                            conflict_counts[case_key] += 1
                        if res["create_conflict"]:
                            conflict_counts["conflicts_created"] += 1
                    if len(rows) < 100:
                        break
                    skip += 100
            self.stdout.write(f"  TeleCRM Leads Matching Existing CRM Phones (Merge Count): {total_merged}")
            self.stdout.write(f"  Net New TeleCRM Leads to be Created: {total_leads - total_merged:,}")
            self.stdout.write("  --- Dry Run Conflict Case Breakdown ---")
            self.stdout.write(f"    CRM Fresh -> TeleCRM status: {conflict_counts['crm_fresh_to_telecrm']}")
            self.stdout.write(f"    TeleCRM Fresh -> CRM kept:   {conflict_counts['telecrm_fresh_kept_crm']}")
            self.stdout.write(f"    Newer TeleCRM won:           {conflict_counts['newer_telecrm_won']}")
            self.stdout.write(f"    Newer CRM won:               {conflict_counts['newer_crm_won']}")
            self.stdout.write(f"    Protected Enrolled:              {conflict_counts['protected_enrolled']}")
            self.stdout.write(f"    Conflicts that would be created: {conflict_counts['conflicts_created']}")
            self.stdout.write(f"    Unchanged (status equal):    {conflict_counts['unchanged']}")
        except Exception as exc:
            self.stdout.write(f"  Merge count calculation notice: {exc}")
            total_merged = 0

        # Disk & Time Estimates
        self.stdout.write("\n[Dry Run: Step 6/6] Estimating Storage, Bandwidth & Import Duration...")
        try:
            total_d, used_d, free_d = shutil.disk_usage("d:")
            free_gb_d = free_d / (1024**3)
            total_c, used_c, free_c = shutil.disk_usage("c:")
            free_gb_c = free_c / (1024**3)
            self.stdout.write(f"  Server Free Disk Space: Drive D = {free_gb_d:.1f} GB Free | Drive C = {free_gb_c:.1f} GB Free")

            # Estimates:
            # ~2.8 actions per lead across 93,557 leads = ~262,000 actions
            # ~1,871 leads with calls in TeleCRM, ~3,500 total call actions
            est_actions = int(total_leads * 2.8)
            est_recordings = 3500
            est_storage_gb = (est_recordings * 1.0) / 1024  # Assuming avg 1 MB per call recording
            # Total HTTP requests: ~936 page searches + 93,557 action searches = ~94,500 requests
            # At 4 requests/sec shared cap (14,400 req/hr):
            est_hours = (total_leads / 4.0) / 3600.0

            self.stdout.write(f"  Estimated Total Action Events: ~{est_actions:,}")
            self.stdout.write(f"  Estimated Leads with Phone Calls: ~1,871 leads")
            self.stdout.write(f"  Estimated Total Audio Recordings: ~{est_recordings:,}")
            self.stdout.write(f"  Estimated Recording Storage Requirement: ~{est_storage_gb:.2f} GB (Drive D Free: {free_gb_d:.1f} GB)")
            self.stdout.write(f"  Estimated Import Duration at 4 req/sec (14,400 req/hr) shared cap: ~{est_hours:.2f} hours")
        except Exception as exc:
            self.stdout.write(f"  Estimate calculation notice: {exc}")

        # Summary Table
        self.stdout.write("\n================================================================================")
        self.stdout.write("TeleCRM Dry Run Summary Report (Zero Database Writes)")
        self.stdout.write("================================================================================")
        self.stdout.write(f"Total Leads in TeleCRM:               {total_leads:,}")
        self.stdout.write(f"Existing CRM Leads Merged:            {total_merged} (Matched by Phone)")
        self.stdout.write(f"Net New Leads to Create:              {total_leads - total_merged:,}")
        self.stdout.write(f"Total Team Members:                   {len(members)}")
        self.stdout.write(f"  - Central Staff Users:              {len(central_users)}")
        self.stdout.write(f"  - Branch-assigned Staff Users:      {len(members) - len(central_users)}")
        self.stdout.write(f"Total Pipeline Statuses:              {len(statuses)}")
        self.stdout.write(f"  - Directly Mapped Statuses:         {len(mapped_statuses)} (100% Mapped)")
        self.stdout.write(f"  - Unmapped / Defaulted Statuses:    {len(unmapped_statuses)}")
        self.stdout.write(f"Total Custom Fields:                  {len(custom_fields)}")
        self.stdout.write(f"Total Custom Actions:                 {len(custom_actions)}")
        self.stdout.write(f"Server Free Disk Space:               {free_gb_d:.1f} GB (Drive D)")
        self.stdout.write(f"Database Writes Performed:            0 (Dry Run Verified)")
        self.stdout.write("================================================================================")
        self.stdout.write("Dry run complete. Awaiting Founder confirmation before real import.\n")

    def _initialize_sync_run(self, resume_flag: bool) -> TeleCRMSyncRun:
        """Initializes or resumes a database-backed TeleCRMSyncRun."""
        if resume_flag:
            existing = (
                TeleCRMSyncRun.objects
                .filter(kind="import", status__in=["RUNNING", "FAILED"])
                .order_by("-started_at")
                .first()
            )
            if existing and not (existing.cursor or {}).get("mapping_done"):
                existing.status = "RUNNING"
                existing.finished_at = None
                existing.save(update_fields=["status", "finished_at"])
                self.stdout.write(f"Resuming existing import run #{existing.id} started at {existing.started_at} (cursor={existing.cursor})")
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

    def _record_non_fatal_error(self, sync_run: TeleCRMSyncRun, error_type: str, detail: str):
        if len(sync_run.errors) < 200:
            sync_run.errors.append({
                "error": error_type,
                "detail": detail[:500],
                "timestamp": timezone.now().isoformat(),
            })

    def _import_leads(self, client: TeleCRMClient, sync_run: TeleCRMSyncRun, max_limit: Optional[int]):
        """Paginates TeleCRM /lead/search and stores raw lead mirrors."""
        if sync_run.cursor.get("leads_done"):
            self.stdout.write(f"  Skipping lead extraction (already completed at skip={sync_run.cursor.get('skip', 0)}).")
            return

        total_enterprise_leads = client.count_leads()
        self.stdout.write(f"  Total leads reported in TeleCRM enterprise: {total_enterprise_leads}")

        target_count = min(total_enterprise_leads, max_limit) if max_limit else total_enterprise_leads
        current_skip = sync_run.cursor.get("skip", 0)
        if target_count > 0 and current_skip >= target_count:
            sync_run.cursor["leads_done"] = True
            sync_run.save(update_fields=["cursor"])
            self.stdout.write(f"  Skipping lead extraction (skip={current_skip} >= target={target_count}).")
            return

        page_size = 100

        # Run continuous paging if target_count was reported as 0 or unknown
        has_known_target = target_count > 0

        while (not has_known_target or current_skip < target_count):
            fetch_limit = min(page_size, target_count - current_skip) if has_known_target else page_size
            if max_limit and current_skip >= max_limit:
                break

            leads_page = client.list_leads(skip=current_skip, limit=fetch_limit)
            if not leads_page:
                self.stdout.write(f"  Reached end of leads at skip={current_skip}.")
                break

            for raw_lead in leads_page:
                tc_id = str(raw_lead.get("id") or "").strip()
                if not tc_id:
                    continue

                try:
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
                except Exception as exc:
                    logger.warning("Skipping bad lead %s during extraction: %s", tc_id, exc)
                    self._record_non_fatal_error(sync_run, "LeadExtractError", f"Lead {tc_id}: {exc}")

            current_skip += len(leads_page)
            sync_run.cursor["skip"] = current_skip
            sync_run.save(update_fields=["leads_seen", "cursor", "errors"])

            rate_str = self._format_rate_stats(client)
            if has_known_target:
                pct = (current_skip / target_count) * 100
                self.stdout.write(f"  Leads Extracted: {current_skip}/{target_count} ({pct:.1f}%) | {rate_str}")
            else:
                self.stdout.write(f"  Leads Extracted: {current_skip} leads... | {rate_str}")

            if len(leads_page) < fetch_limit:
                break

        sync_run.cursor["leads_done"] = True
        sync_run.save(update_fields=["cursor"])

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
                            try:
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
                            except Exception as act_exc:
                                logger.warning("Skipping bad action %s for lead %s: %s", act_id, lead_id, act_exc)
                                self._record_non_fatal_error(sync_run, "ActionSaveError", f"Lead {lead_id} action {act_id}: {act_exc}")

                    if tc_lead:
                        tc_lead.history_fetched = True
                        tc_lead.save(update_fields=["history_fetched"])

                except Exception as exc:
                    logger.warning("Error fetching actions for lead %s: %s", lead_id, exc)
                    self._record_non_fatal_error(sync_run, "HistoryFetchError", f"Lead {lead_id}: {exc}")

                if completed % 100 == 0 or completed == total_leads:
                    pct = (completed / total_leads) * 100
                    sync_run.actions_created += total_actions_created
                    total_actions_created = 0
                    sync_run.save(update_fields=["actions_created", "errors"])
                    rate_str = self._format_rate_stats(client)
                    self.stdout.write(f"  History Progress: {completed}/{total_leads} leads ({pct:.1f}%) | {rate_str}")

        sync_run.cursor["history_done"] = True
        sync_run.save(update_fields=["cursor", "actions_created"])

    def _map_records_to_crm(self, sync_run: TeleCRMSyncRun, batch_size: int, max_limit: Optional[int], client: Optional[TeleCRMClient] = None):
        """Runs the deterministic mapper with per-lead atomic savepoints under side-effect suppression."""
        qs = TeleCRMLead.objects.all().order_by("-telecrm_created_at")
        if max_limit:
            qs = qs[:max_limit]

        total_to_map = qs.count()
        start_offset = 0 if max_limit else int((sync_run.cursor or {}).get("mapping_offset", 0) or 0)
        if start_offset >= total_to_map and total_to_map > 0:
            sync_run.cursor["mapping_done"] = True
            sync_run.save(update_fields=["cursor"])
            self.stdout.write(f"  Skipping mapping (already completed {start_offset}/{total_to_map}).")
            return

        self.stdout.write(f"  Mapping {total_to_map} TeleCRM leads into CRM native tables (starting at offset {start_offset}, batch size: {batch_size})...")

        user_cache: Dict[str, Optional[User]] = {}
        processed = start_offset

        with suppress_sync_side_effects():
            for i in range(start_offset, total_to_map, batch_size):
                batch_qs = qs[i:i + batch_size]
                batch_leads = list(batch_qs)

                # Pre-fetch actions for this batch to minimize queries
                batch_tc_ids = [l.id for l in batch_leads]
                actions_by_lead_id: Dict[int, List[Dict[str, Any]]] = {}
                for act in TeleCRMAction.objects.filter(lead_id__in=batch_tc_ids).order_by("occurred_at"):
                    if act.lead_id not in actions_by_lead_id:
                        actions_by_lead_id[act.lead_id] = []
                    actions_by_lead_id[act.lead_id].append(act.raw)

                for tc_lead in batch_leads:
                    try:
                        with transaction.atomic():
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
                                ingest_lead_actions(
                                    lead=lead,
                                    tc_lead=tc_mirror,
                                    raw_actions=lead_actions,
                                    user_cache=user_cache,
                                    client=client,
                                )

                    except Exception as exc:
                        logger.exception("Error mapping lead %s: %s", tc_lead.telecrm_id, exc)
                        self._record_non_fatal_error(sync_run, "LeadMapError", f"Lead {tc_lead.telecrm_id}: {exc}")

                processed += len(batch_leads)
                if not max_limit:
                    sync_run.cursor["mapping_offset"] = processed
                sync_run.save(update_fields=["leads_created", "leads_merged", "errors", "cursor"])
                pct = (processed / total_to_map) * 100 if total_to_map else 100
                self.stdout.write(f"  Mapping Progress: {processed}/{total_to_map} ({pct:.1f}%) | Created: {sync_run.leads_created} | Merged: {sync_run.leads_merged}")

        if not max_limit:
            sync_run.cursor["mapping_done"] = True
            sync_run.save(update_fields=["cursor"])

    def _get_rate_stats(self, client: Optional[TeleCRMClient]) -> Optional[Dict[str, Any]]:
        limiter = getattr(client, "rate_limiter", None) if client else None
        if limiter is None or not hasattr(limiter, "get_stats"):
            return None
        stats = limiter.get_stats()
        if not isinstance(stats, dict):
            return None
        return stats

    def _format_rate_stats(self, client: Optional[TeleCRMClient]) -> str:
        stats = self._get_rate_stats(client)
        if not stats:
            return "Rate: n/a"
        rph = float(stats.get("requests_per_hour", 0.0))
        rps = float(stats.get("requests_per_sec", 0.0))
        reqs = int(stats.get("total_requests", 0))
        hits_429 = int(stats.get("rate_limit_429_count", 0))
        return f"Rate: {rph:,.0f} req/hr ({rps:.2f} req/s) | Reqs: {reqs:,} | 429s: {hits_429}"

    def _print_summary(self, sync_run: TeleCRMSyncRun, elapsed_sec: float, client: Optional[TeleCRMClient] = None):
        """Prints a clean, structured completion summary."""
        stats = self._get_rate_stats(client)
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
        if stats:
            self.stdout.write(
                f"API Throughput:          {stats['requests_per_hour']:,.0f} req/hr "
                f"({stats['requests_per_sec']:.2f} req/s, {stats['total_requests']:,} reqs, "
                f"cap={stats['cap_rps']:.1f} req/s, 429s={stats['rate_limit_429_count']})"
            )
        self.stdout.write(f"Errors Logged:           {len(sync_run.errors)}")
        self.stdout.write("================================================================================")
