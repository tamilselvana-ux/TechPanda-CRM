from datetime import timedelta
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from leads.models import Lead, LeadStatus


class TeleCRMLead(models.Model):
    """
    Mirror table for raw TeleCRM leads and synchronization bookkeeping.
    The CRM native Lead model remains the source of truth for all business operations.
    """
    telecrm_id = models.CharField(max_length=64, unique=True, db_index=True)
    phone = models.CharField(max_length=32, db_index=True, blank=True, default='')
    raw = models.JSONField(default=dict, blank=True)
    crm_lead = models.ForeignKey(
        Lead,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='telecrm_mirrors',
        help_text="Corresponding TechPanda CRM native Lead instance"
    )
    telecrm_created_at = models.DateTimeField(null=True, blank=True, db_index=True)
    telecrm_modified_at = models.DateTimeField(null=True, blank=True)
    last_synced_status = models.CharField(max_length=64, blank=True, default='', help_text="Status at last completed sync for dual-edit conflict detection")
    history_fetched = models.BooleanField(default=False, db_index=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'telecrm_lead'
        ordering = ['-telecrm_created_at']
        verbose_name = 'TeleCRM Lead'
        verbose_name_plural = 'TeleCRM Leads'

    def __str__(self):
        return f"{self.telecrm_id} ({self.phone or 'No Phone'})"


class TeleCRMAction(models.Model):
    """
    Mirror table for individual actions and timeline events imported from TeleCRM.
    """
    telecrm_id = models.CharField(max_length=64, unique=True, db_index=True)
    lead = models.ForeignKey(
        TeleCRMLead,
        on_delete=models.CASCADE,
        related_name='actions'
    )
    type = models.CharField(max_length=64, db_index=True)
    occurred_at = models.DateTimeField(db_index=True)
    employee_uid = models.CharField(max_length=128, blank=True, default='')
    raw = models.JSONField(default=dict, blank=True)
    crm_object_type = models.CharField(max_length=64, blank=True, default='')
    crm_object_id = models.CharField(max_length=64, blank=True, default='')
    mapped_ok = models.BooleanField(default=False, db_index=True)
    error = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'telecrm_action'
        ordering = ['-occurred_at']
        verbose_name = 'TeleCRM Action'
        verbose_name_plural = 'TeleCRM Actions'

    def __str__(self):
        return f"{self.type} - {self.telecrm_id} ({self.occurred_at})"

    @property
    def display_duration(self) -> str:
        raw_dict = self.raw if isinstance(self.raw, dict) else {}
        dur = raw_dict.get("duration")
        if dur is None:
            dur = raw_dict.get("call_duration")
        if dur is not None:
            try:
                sec = int(dur)
                return f"{sec // 60}m {sec % 60}s" if sec >= 60 else f"{sec}s"
            except (ValueError, TypeError):
                return str(dur)
        return "0s"

    @property
    def display_text(self) -> str:
        raw_dict = self.raw if isinstance(self.raw, dict) else {}
        return str(
            raw_dict.get("text")
            or raw_dict.get("notes")
            or raw_dict.get("note")
            or raw_dict.get("message")
            or raw_dict.get("messageText")
            or raw_dict.get("richText")
            or raw_dict.get("reassignmentNote")
            or ""
        )

    @property
    def display_status(self) -> str:
        raw_dict = self.raw if isinstance(self.raw, dict) else {}
        return str(raw_dict.get("status") or raw_dict.get("feedback") or "")

    @property
    def display_old_status(self) -> str:
        raw_dict = self.raw if isinstance(self.raw, dict) else {}
        return str(raw_dict.get("fromStatusid") or raw_dict.get("old_status") or raw_dict.get("from") or "New")

    @property
    def display_new_status(self) -> str:
        raw_dict = self.raw if isinstance(self.raw, dict) else {}
        return str(raw_dict.get("toStatusid") or raw_dict.get("new_status") or raw_dict.get("to") or "-")

    @property
    def display_assigned_to(self) -> str:
        raw_dict = self.raw if isinstance(self.raw, dict) else {}
        return str(raw_dict.get("assigned_to") or raw_dict.get("assignedto") or self.employee_uid or "-")

    @property
    def campaign_name(self) -> str:
        raw_dict = self.raw if isinstance(self.raw, dict) else {}
        return str(raw_dict.get("campaign_name") or raw_dict.get("campaignName") or raw_dict.get("pageName") or "")

    @property
    def form_name(self) -> str:
        raw_dict = self.raw if isinstance(self.raw, dict) else {}
        return str(raw_dict.get("form_name") or raw_dict.get("formName") or "")

    @property
    def display_summary(self) -> str:
        act_type = (self.type or "").upper()
        if "CALL" in act_type:
            parts = [f"Call: {self.display_duration}"]
            if self.display_status:
                parts.append(f"({self.display_status})")
            if self.display_text:
                parts.append(f"- {self.display_text}")
            return " ".join(parts)
        elif "WHATSAPP" in act_type:
            direction = "Outgoing" if "OUTGOING" in act_type else "Incoming"
            return f"{direction} WhatsApp: {self.display_text}" if self.display_text else f"{direction} WhatsApp Message"
        elif "NOTE" in act_type:
            prefix = "System Note" if "SYSTEM" in act_type else "Note"
            return f"{prefix}: {self.display_text}" if self.display_text else prefix
        elif "STATUS" in act_type:
            return f"Status update: {self.display_old_status} -> {self.display_new_status}"
        elif "ASSIGN" in act_type:
            return f"Lead assigned to {self.display_assigned_to}"
        elif "FACEBOOK" in act_type or "META" in act_type:
            parts = ["Meta Ad Lead Intake"]
            if self.campaign_name:
                parts.append(f"Page: {self.campaign_name}")
            if self.form_name:
                parts.append(f"Form: {self.form_name}")
            return " - ".join(parts)
        elif "FIELD" in act_type:
            raw_dict = self.raw if isinstance(self.raw, dict) else {}
            f_id = raw_dict.get("fieldid") or "field"
            return f"Field updated ({f_id}): {raw_dict.get('from', '')} -> {raw_dict.get('to', '')}"
        else:
            return self.display_text or f"TeleCRM Event: {self.type or 'Action'}"


class TeleCRMUser(models.Model):
    """
    Mapping table linking TeleCRM internal employee UIDs to CRM User accounts via email.
    """
    uid = models.CharField(max_length=128, unique=True, db_index=True)
    email = models.CharField(max_length=255, blank=True, default='', db_index=True)
    name = models.CharField(max_length=255, blank=True, default='')
    crm_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='telecrm_users',
        help_text="Matched TechPanda CRM user account"
    )

    class Meta:
        db_table = 'telecrm_user'
        ordering = ['name', 'email']
        verbose_name = 'TeleCRM User Mapping'
        verbose_name_plural = 'TeleCRM User Mappings'

    def __str__(self):
        return f"{self.name or self.email or self.uid} -> {self.crm_user.username if self.crm_user else 'Unmatched'}"


class TeleCRMStatusMap(models.Model):
    """
    Editable mapping matrix linking TeleCRM pipeline status names/IDs to CRM LeadStatus choices.
    """
    telecrm_status_id = models.CharField(max_length=64, blank=True, default='')
    telecrm_status_name = models.CharField(max_length=128, unique=True, db_index=True)
    crm_status = models.CharField(
        max_length=64,
        choices=LeadStatus.choices,
        default=LeadStatus.NEW
    )
    notes = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'telecrm_status_map'
        ordering = ['telecrm_status_name']
        verbose_name = 'TeleCRM Status Mapping'
        verbose_name_plural = 'TeleCRM Status Mappings'

    def __str__(self):
        return f"{self.telecrm_status_name} -> {self.crm_status}"


class TeleCRMSyncRun(models.Model):
    """
    Execution run logs and concurrency locks for one-time imports and cron-based incremental syncs.
    """
    KIND_CHOICES = [
        ('import', 'Initial Import'),
        ('sync', 'Live Incremental Sync'),
    ]
    STATUS_CHOICES = [
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    kind = models.CharField(max_length=32, choices=KIND_CHOICES, default='sync', db_index=True)
    started_at = models.DateTimeField(default=timezone.now, db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    cursor = models.JSONField(default=dict, blank=True)
    leads_seen = models.IntegerField(default=0)
    leads_created = models.IntegerField(default=0)
    leads_merged = models.IntegerField(default=0)
    actions_created = models.IntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='RUNNING', db_index=True)

    class Meta:
        db_table = 'telecrm_sync_run'
        ordering = ['-started_at']
        verbose_name = 'TeleCRM Sync Run'
        verbose_name_plural = 'TeleCRM Sync Runs'

    def __str__(self):
        return f"{self.kind} ({self.status}) - started {self.started_at}"


class SyncConflict(models.Model):
    """
    Records status conflicts between TechPanda CRM and TeleCRM for manual review
    (e.g., Enrolled protection or both sides edited since last successful sync).
    """
    STATUS_OPEN = 'OPEN'
    STATUS_KEPT_CRM = 'KEPT_CRM'
    STATUS_USED_TELECRM = 'USED_TELECRM'
    RESOLUTION_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_KEPT_CRM, 'Kept CRM'),
        (STATUS_USED_TELECRM, 'Used TeleCRM'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='sync_conflicts')
    telecrm_lead = models.ForeignKey(TeleCRMLead, null=True, blank=True, on_delete=models.SET_NULL, related_name='conflicts')
    crm_status = models.CharField(max_length=64)
    crm_status_at = models.DateTimeField(null=True, blank=True)
    telecrm_status = models.CharField(max_length=64)
    telecrm_status_at = models.DateTimeField(null=True, blank=True)
    telecrm_status_label = models.CharField(max_length=128, blank=True, default='')
    applied_status = models.CharField(max_length=64)
    rule_applied = models.CharField(max_length=64, blank=True, default='')
    status = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, default=STATUS_OPEN, db_index=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='resolved_sync_conflicts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'telecrm_sync_conflict'
        ordering = ['-created_at']
        verbose_name = 'TeleCRM Sync Conflict'
        verbose_name_plural = 'TeleCRM Sync Conflicts'

    def __str__(self):
        return f"Lead #{self.lead_id}: CRM({self.crm_status}) vs TeleCRM({self.telecrm_status}) [{self.status}]"


class SyncLock(models.Model):
    """
    Database-backed distributed lock and sync-enablement state shared between
    telecrm_import and telecrm_sync. Held by telecrm_import for its entire run;
    telecrm_sync exits cleanly whenever the import lock is held.
    """
    DEFAULT_NAME = 'telecrm_global'

    name = models.CharField(max_length=64, unique=True, default=DEFAULT_NAME)
    holder = models.CharField(max_length=64, blank=True, default='')
    run_id = models.IntegerField(null=True, blank=True)
    is_locked = models.BooleanField(default=False, db_index=True)
    sync_enabled = models.BooleanField(
        default=False,
        help_text='Enabled automatically only after telecrm_import finishes successfully'
    )
    acquired_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'telecrm_sync_lock'
        verbose_name = 'TeleCRM Sync Lock'
        verbose_name_plural = 'TeleCRM Sync Locks'

    def __str__(self):
        state = f"LOCKED by {self.holder} (run={self.run_id})" if self.is_locked else "UNLOCKED"
        return f"{self.name}: {state} | sync_enabled={self.sync_enabled}"

    @classmethod
    def acquire(
        cls,
        name: str = DEFAULT_NAME,
        holder: str = 'import',
        run_id: int = None,
        ttl_hours: int = 24,
        disable_sync_while_held: bool = False,
    ):
        now = timezone.now()
        with transaction.atomic():
            cls.objects.get_or_create(name=name)
            lock = cls.objects.select_for_update().get(name=name)
            if lock.is_locked and (lock.expires_at is None or lock.expires_at > now):
                return False, lock
            lock.is_locked = True
            lock.holder = holder
            lock.run_id = run_id
            lock.acquired_at = now
            lock.expires_at = now + timedelta(hours=ttl_hours)
            if disable_sync_while_held:
                lock.sync_enabled = False
            lock.save(update_fields=[
                'is_locked', 'holder', 'run_id', 'acquired_at', 'expires_at', 'sync_enabled', 'updated_at'
            ])
            return True, lock

    @classmethod
    def release(
        cls,
        name: str = DEFAULT_NAME,
        holder: str = None,
        enable_sync: bool = None,
    ) -> None:
        with transaction.atomic():
            lock = cls.objects.select_for_update().filter(name=name).first()
            if not lock:
                return
            if holder is None or lock.holder == holder:
                lock.is_locked = False
                lock.holder = ''
                lock.run_id = None
                lock.acquired_at = None
                lock.expires_at = None
            if enable_sync is not None:
                lock.sync_enabled = bool(enable_sync)
            lock.save(update_fields=[
                'is_locked', 'holder', 'run_id', 'acquired_at', 'expires_at', 'sync_enabled', 'updated_at'
            ])

    @classmethod
    def is_held(cls, name: str = DEFAULT_NAME, holder: str = None) -> bool:
        now = timezone.now()
        qs = cls.objects.filter(name=name, is_locked=True).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )
        if holder is not None:
            qs = qs.filter(holder=holder)
        return qs.exists()

    @classmethod
    def is_sync_enabled(cls, name: str = DEFAULT_NAME) -> bool:
        if getattr(settings, 'TELECRM_SYNC_ENABLED', False):
            return True
        return cls.objects.filter(name=name, sync_enabled=True).exists()
