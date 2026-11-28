import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.management.base import BaseCommand
from drive.models import CallRecording
from telecrm_sync.client import TeleCRMClient
from telecrm_sync.mapper import _download_and_link_recording
from telecrm_sync.models import TeleCRMLead

logger = logging.getLogger("telecrm_sync")


class Command(BaseCommand):
    help = "Idempotent command to backfill/download TeleCRM call recordings into local private_media storage."

    def add_arguments(self, parser):
        parser.add_argument("--max", type=int, default=None, help="Maximum recordings to attempt in this run")
        parser.add_argument("--workers", type=int, default=3, help="Concurrent download threads (default: 3)")
        parser.add_argument("--dry-run", action="store_true", help="Count pending/failed recordings without downloading")
        parser.add_argument("--token", type=str, default=None, help="Override TELECRM_TOKEN")
        parser.add_argument("--enterprise-id", type=str, default=None, help="Override TELECRM_ENTERPRISE_ID")

    def handle(self, *args, **options):
        max_limit = options.get("max")
        workers = max(1, options.get("workers") or 3)
        dry_run = options.get("dry_run", False)

        qs = (
            CallRecording.objects
            .filter(drive_file_id__startswith="telecrm_ch_", archive_status__in=["PENDING", "FAILED"])
            .exclude(drive_url="")
            .select_related("lead", "call_history", "telecaller")
            .order_by("-recording_date")
        )
        total_pending = qs.count()
        self.stdout.write(f"TeleCRM recordings queued for backfill: {total_pending}")

        if dry_run or total_pending == 0:
            return

        if max_limit:
            qs = qs[:max_limit]
        items = list(qs)

        client = TeleCRMClient(token=options.get("token"), enterprise_id=options.get("enterprise_id"))
        stats = {"downloaded": 0, "failed": 0, "bytes": 0, "errors": []}

        def process_one(rec: CallRecording):
            if not rec.lead or not rec.call_history:
                return
            tc_lead = TeleCRMLead.objects.filter(crm_lead=rec.lead).first()
            if not tc_lead:
                return
            a_type = "OUTGOING_CALL" if rec.direction == "outgoing" else "INCOMING_CALL"
            _download_and_link_recording(
                lead=rec.lead,
                tc_lead=tc_lead,
                ch=rec.call_history,
                rec_obj={"filePath": rec.drive_url, "name": rec.file_name},
                occurred_dt=rec.recording_date or rec.created_at,
                duration_sec=rec.duration_seconds,
                a_type=a_type,
                actor_user=rec.telecaller,
                client=client,
                recording_stats=stats,
                download_recordings=True,
            )

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(process_one, rec) for rec in items]
            for idx, fut in enumerate(as_completed(futures), 1):
                try:
                    fut.result()
                except Exception as exc:
                    logger.warning("Recording backfill error: %s", exc)
                if idx % 50 == 0 or idx == len(items):
                    self.stdout.write(
                        f"  Backfill Progress: {idx}/{len(items)} | Downloaded: {stats['downloaded']} | Failed: {stats['failed']}"
                    )

        total_gb = stats["bytes"] / (1024 ** 3)
        self.stdout.write(
            f"Backfill Complete: Downloaded={stats['downloaded']}, Failed={stats['failed']}, Total={total_gb:.4f} GB"
        )
