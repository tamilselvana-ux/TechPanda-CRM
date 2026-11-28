import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from telecrm_sync.client import TeleCRMAuthError, TeleCRMClient, TeleCRMError
from telecrm_sync.mapper import (
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
    help = "Incremental live sync command from TeleCRM into TechPanda CRM (cron-driven with database lock)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Run even if TELECRM_SYNC_ENABLED is False in settings, and clear stale/active locks"
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
        parser.add_argument(
            "--window-minutes",
            type=int,
            default=None,
            help="Override lookback window in minutes"
        )
        parser.add_argument(
            "--max-pages",
            type=int,
            default=5,
            help="Maximum pages of new leads to check per cron run (default: 5, max 500 leads)"
        )

    def handle(self, *args, **options):
        force_flag: bool = options["force"]
        token: Optional[str] = options["token"]
        enterprise_id: Optional[str] = options["enterprise_id"]
        window_minutes_override: Optional[int] = options["window_minutes"]
        max_pages: int = max(1, options.get("max_pages") or 5)

        # 1. Feature Flag Gate
        sync_enabled = getattr(settings, "TELECRM_SYNC_ENABLED", False)
        if not sync_enabled and not force_flag:
            self.stdout.write("Notice: TELECRM_SYNC_ENABLED is False. Exiting without action. Use --force to override.")
            return

        # 2. Concurrency Lock: Check if another sync is currently RUNNING
        stale_threshold = timezone.now() - timedelta(minutes=10)
        active_run = TeleCRMSyncRun.objects.filter(kind="sync", status="RUNNING", started_at__gte=stale_threshold).first()
        if active_run:
            self.stdout.write(
                f"Notice: Another TeleCRM sync task (Run #{active_run.id}) started at {active_run.started_at} is currently active. Exiting to avoid concurrency collision."
            )
            return

        # Clear stale locks older than 10 minutes
        TeleCRMSyncRun.objects.filter(kind="sync", status="RUNNING", started_at__lt=stale_threshold).update(
            status="FAILED",
            finished_at=timezone.now()
        )

        client = TeleCRMClient(token=token, enterprise_id=enterprise_id)
        if not client.token:
            self.stdout.write("Error: TELECRM_TOKEN is not configured. Exiting.")
            return

        # Step 0: Ensure team members and pipeline status metadata are synchronized
        self._sync_metadata(client)

        start_time = time.time()
        window_to = timezone.now()

        # 3. Determine Incremental Time Window
        if window_minutes_override:
            window_from = window_to - timedelta(minutes=window_minutes_override)
        else:
            last_run = TeleCRMSyncRun.objects.filter(kind="sync", status="COMPLETED").order_by("-started_at").first()
            if last_run and (last_run.finished_at or last_run.started_at):
                ref_time = last_run.finished_at or last_run.started_at
                # 10 minutes overlap for clock skew safety
                window_from = ref_time - timedelta(minutes=10)
            else:
                # First run lookback fallback: 2 hours (efficient incremental intake)
                window_from = window_to - timedelta(hours=2)

        sync_run = TeleCRMSyncRun.objects.create(
            kind="sync",
            status="RUNNING",
            started_at=window_to,
            cursor={
                "window_from": window_from.isoformat(),
                "window_to": window_to.isoformat()
            }
        )

        self.stdout.write(f"Sync Run #{sync_run.id} started. Window: {window_from.isoformat()} to {window_to.isoformat()}")

        try:
            target_lead_ids: Set[str] = set()
            raw_leads_by_id: Dict[str, Dict[str, Any]] = {}

            # 4. Discover New Leads (newest-first, bounded by max_pages)
            self._discover_new_leads(client, target_lead_ids, raw_leads_by_id, max_pages=max_pages)

            # 5. Discover Leads with Activity in Window
            self._discover_changed_leads(client, window_from, window_to, target_lead_ids, raw_leads_by_id)

            self.stdout.write(f"Total leads identified for update/sync: {len(target_lead_ids)}")
            sync_run.leads_seen = len(target_lead_ids)

            # 6. Fetch New Actions for New/Changed Leads concurrently
            actions_by_lead_id = self._fetch_new_actions(client, target_lead_ids)

            # 7. Map & Ingest into CRM under side-effect suppression
            self._map_sync_batch(sync_run, target_lead_ids, raw_leads_by_id, actions_by_lead_id)

            sync_run.status = "COMPLETED"
            sync_run.finished_at = timezone.now()
            sync_run.save(update_fields=["status", "finished_at", "leads_seen", "leads_created", "leads_merged", "actions_created", "errors"])

            elapsed = time.time() - start_time
            self.stdout.write(
                f"Sync Run #{sync_run.id} COMPLETED in {elapsed:.2f}s | "
                f"Seen: {sync_run.leads_seen} | Created: {sync_run.leads_created} | Merged: {sync_run.leads_merged} | Actions: {sync_run.actions_created}"
            )

        except Exception as exc:
            sync_run.status = "FAILED"
            sync_run.finished_at = timezone.now()
            sync_run.errors.append({"error": "SyncError", "detail": str(exc), "timestamp": timezone.now().isoformat()})
            sync_run.save(update_fields=["status", "finished_at", "errors"])
            logger.exception("TeleCRM sync run %s failed: %s", sync_run.id, exc)
            self._handle_failure_streak(sync_run, exc)
            raise CommandError(f"Sync failed: {exc}") from exc

    def _sync_metadata(self, client: TeleCRMClient):
        """Ensures team members and pipeline statuses from TeleCRM are up to date."""
        try:
            members = client.get_team_members()
            for m in members:
                uid = str(m.get("uid") or m.get("id") or m.get("userId") or "").strip()
                email = str(m.get("email") or "").strip().lower()
                name = str(m.get("name") or "").strip()
                if not uid and not email:
                    continue
                crm_u = None
                if email:
                    crm_u = User.objects.filter(email__iexact=email).first()
                TeleCRMUser.objects.update_or_create(
                    uid=uid or email,
                    defaults={"email": email, "name": name, "crm_user": crm_u}
                )
        except Exception as exc:
            logger.warning("TeleCRM team members metadata sync skipped: %s", exc)

        try:
            pipeline = client.get_lead_stage_pipeline()
            statuses = pipeline.get("statuses") or []
            for st in statuses:
                s_id = str(st.get("id") or "").strip()
                label = str(st.get("label") or st.get("name") or "").strip()
                if not label:
                    continue
                crm_st = resolve_crm_status(label, s_id)
                TeleCRMStatusMap.objects.update_or_create(
                    telecrm_status_name=label,
                    defaults={"telecrm_status_id": s_id, "crm_status": crm_st}
                )
        except Exception as exc:
            logger.warning("TeleCRM pipeline metadata sync skipped: %s", exc)

    def _discover_new_leads(
        self,
        client: TeleCRMClient,
        target_lead_ids: Set[str],
        raw_leads_by_id: Dict[str, Dict[str, Any]],
        max_pages: int = 5
    ):
        """Pages /lead/search newest-first and stops when encountering all known leads or hitting max_pages limit."""
        skip = 0
        limit = 100
        remaining_pages = max_pages

        while remaining_pages > 0:
            page = client.list_leads(skip=skip, limit=limit)
            if not page:
                break

            known_count = 0
            for lead in page:
                lid = str(lead.get("id") or "").strip()
                if not lid:
                    continue

                if TeleCRMLead.objects.filter(telecrm_id=lid).exists():
                    known_count += 1
                else:
                    target_lead_ids.add(lid)
                    raw_leads_by_id[lid] = lead

            # If all leads on this page are already known, stop paging
            if known_count == len(page):
                break

            skip += len(page)
            remaining_pages -= 1

    def _discover_changed_leads(
        self,
        client: TeleCRMClient,
        start_dt: datetime,
        end_dt: datetime,
        target_lead_ids: Set[str],
        raw_leads_by_id: Dict[str, Dict[str, Any]]
    ):
        """Finds leads with activity in the given time window via POST /lead/search actions filter."""
        skip = 0
        limit = 100

        while True:
            leads, total = client.list_leads_active_between(start_dt, end_dt, skip=skip, limit=limit)
            if not leads:
                break

            for lead in leads:
                lid = str(lead.get("id") or "").strip()
                if lid:
                    target_lead_ids.add(lid)
                    raw_leads_by_id[lid] = lead

            skip += len(leads)
            if skip >= total or len(leads) < limit:
                break

    def _fetch_new_actions(
        self,
        client: TeleCRMClient,
        target_lead_ids: Set[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetches actions newest-first for each lead concurrently, stopping at already-stored action IDs."""
        actions_by_lead_id: Dict[str, List[Dict[str, Any]]] = {}
        if not target_lead_ids:
            return actions_by_lead_id

        # Pre-fetch existing action IDs once on the main thread so worker threads perform zero DB queries
        existing_action_ids = set(
            TeleCRMAction.objects.filter(lead__telecrm_id__in=target_lead_ids)
            .values_list('telecrm_id', flat=True)
        )

        def fetch_for_lead(lid: str) -> Tuple[str, List[Dict[str, Any]]]:
            lead_acts = []
            skip = 0
            limit = 100
            while True:
                page, total = client.get_lead_actions(lid, skip=skip, limit=limit)
                if not page:
                    break
                stop_paging = False
                for act in page:
                    act_id = str(act.get("id") or "").strip()
                    if not act_id:
                        continue
                    if act_id in existing_action_ids:
                        stop_paging = True
                        break
                    lead_acts.append(act)
                if stop_paging:
                    break
                skip += len(page)
                if skip >= total or len(page) < limit:
                    break
            return lid, lead_acts

        from django.db import connection
        max_workers = 1 if connection.vendor == 'sqlite' else min(10, max(1, len(target_lead_ids)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(fetch_for_lead, lid) for lid in target_lead_ids]
            for fut in as_completed(futures):
                try:
                    lid, lead_acts = fut.result()
                    actions_by_lead_id[lid] = lead_acts
                except Exception as exc:
                    logger.warning("Error fetching actions for lead: %s", exc)

        return actions_by_lead_id

    def _map_sync_batch(
        self,
        sync_run: TeleCRMSyncRun,
        target_lead_ids: Set[str],
        raw_leads_by_id: Dict[str, Dict[str, Any]],
        actions_by_lead_id: Dict[str, List[Dict[str, Any]]]
    ):
        """Maps discovered leads and actions into CRM models in a single atomic transaction."""
        user_cache: Dict[str, Optional[User]] = {}

        with suppress_sync_side_effects():
            with transaction.atomic():
                for lid in target_lead_ids:
                    raw_lead = raw_leads_by_id.get(lid)
                    if not raw_lead:
                        # If raw_lead wasn't in recent search page, load from mirror
                        tc_mirror = TeleCRMLead.objects.filter(telecrm_id=lid).first()
                        raw_lead = tc_mirror.raw if tc_mirror else None

                    if not raw_lead:
                        continue

                    lead_actions = actions_by_lead_id.get(lid, [])

                    crm_lead, tc_lead, was_created = ingest_or_merge_lead(
                        raw_lead=raw_lead,
                        actions=lead_actions,
                        user_cache=user_cache
                    )

                    if was_created:
                        sync_run.leads_created += 1
                    else:
                        sync_run.leads_merged += 1

                    if lead_actions:
                        mapped_count = ingest_lead_actions(
                            lead=crm_lead,
                            tc_lead=tc_lead,
                            raw_actions=lead_actions,
                            user_cache=user_cache
                        )
                        sync_run.actions_created += mapped_count

    def _handle_failure_streak(self, sync_run: TeleCRMSyncRun, exc: Exception):
        """Circuit breaker: alerts administrators if 3 consecutive sync runs fail."""
        recent_runs = list(TeleCRMSyncRun.objects.filter(kind="sync").order_by("-started_at")[:3])
        if len(recent_runs) >= 3 and all(r.status == "FAILED" for r in recent_runs):
            alert_msg = (
                f"ALERT: TeleCRM sync circuit breaker tripped. "
                f"The last 3 consecutive sync runs have failed. "
                f"Most recent error in Run #{sync_run.id}: {exc}"
            )
            logger.critical(alert_msg)
            try:
                mail_admins(
                    subject="CRITICAL: TeleCRM Sync Failure Streak Alert",
                    message=alert_msg,
                    fail_silently=True
                )
            except Exception:
                pass
