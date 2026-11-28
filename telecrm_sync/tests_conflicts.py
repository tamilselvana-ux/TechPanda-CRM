from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from activities.models import Activity
from branches.models import Branch
from calls.models import CallHistory
from drive.models import CallRecording
from leads.models import Lead, LeadStatus, LeadStatusHistory
from telecrm_sync.mapper import (
    ingest_lead_actions,
    ingest_or_merge_lead,
    sync_telecrm_lead_payload,
)
from telecrm_sync.models import SyncConflict, TeleCRMLead

User = get_user_model()


class TeleCRMConflictRulesTests(TestCase):
    def setUp(self):
        self.branch_tn, _ = Branch.objects.get_or_create(name="T. Nagar")
        self.branch_vel, _ = Branch.objects.get_or_create(name="Velachery")

        self.admin = User.objects.create_user(
            username="admin_u", email="admin@test.com", password="pass",
            role="SUPERADMIN", is_superuser=True, is_staff=True
        )
        self.sales_head = User.objects.create_user(
            username="sh_u", email="sh@test.com", password="pass",
            role="SALES_HEAD"
        )
        self.bh_tn = User.objects.create_user(
            username="bh_tn", email="bh_tn@test.com", password="pass",
            role="BRANCH_HEAD", branch=self.branch_tn
        )
        self.bh_vel = User.objects.create_user(
            username="bh_vel", email="bh_vel@test.com", password="pass",
            role="BRANCH_HEAD", branch=self.branch_vel
        )
        self.tc_active = User.objects.create_user(
            username="tc_active", email="tc_active@test.com", password="pass",
            role="TELECALLER", branch=self.branch_tn, is_active=True
        )
        self.tc_inactive = User.objects.create_user(
            username="tc_inactive", email="tc_inactive@test.com", password="pass",
            role="TELECALLER", branch=self.branch_tn, is_active=False
        )
        self.tc_other = User.objects.create_user(
            username="tc_other", email="tc_other@test.com", password="pass",
            role="TELECALLER", branch=self.branch_vel, is_active=True
        )

    def _raw_lead(self, tid, phone, status, status_dt=None, employee="tc_other@test.com", name="Test Lead", email=""):
        ms = int(status_dt.timestamp() * 1000) if status_dt else int(timezone.now().timestamp() * 1000)
        return {
            "id": tid,
            "status": status,
            "employeeid": employee,
            "creationTimestamp": ms,
            "fields": {
                "phone": phone,
                "name": name,
                "email": email,
                "status": status,
                "status_last_updated_on": ms,
                "created_on": ms,
                "modified_on": ms,
            }
        }

    def test_1_fresh_never_overwrites_non_fresh_either_direction(self):
        # 1a. CRM Fresh -> TeleCRM non-Fresh => TeleCRM wins
        lead_a = Lead.objects.create(name="Lead A", phone="9876543210", normalized_phone="9876543210", status=LeadStatus.NEW)
        ingest_or_merge_lead(self._raw_lead("tc_1a", "919876543210", "Interested"))
        lead_a.refresh_from_db()
        self.assertEqual(lead_a.status, LeadStatus.INTERESTED)
        self.assertEqual(SyncConflict.objects.filter(lead=lead_a).count(), 0)

        # 1b. CRM non-Fresh -> TeleCRM Fresh => CRM kept (even if TeleCRM timestamp is newer)
        lead_b = Lead.objects.create(name="Lead B", phone="9876543211", normalized_phone="9876543211", status=LeadStatus.INTERESTED)
        lsh = LeadStatusHistory.objects.create(lead=lead_b, old_status=LeadStatus.NEW, new_status=LeadStatus.INTERESTED)
        LeadStatusHistory.objects.filter(pk=lsh.pk).update(created_at=timezone.now() - timedelta(days=5))
        ingest_or_merge_lead(self._raw_lead("tc_1b", "919876543211", "Fresh", status_dt=timezone.now()))
        lead_b.refresh_from_db()
        self.assertEqual(lead_b.status, LeadStatus.INTERESTED)
        self.assertEqual(SyncConflict.objects.filter(lead=lead_b).count(), 0)

    def test_2_both_non_fresh_latest_status_history_timestamp_wins(self):
        now = timezone.now()
        # 2a. Newer TeleCRM wins; ignore newer lead.updated_at if LeadStatusHistory is older
        lead_a = Lead.objects.create(name="Lead 2A", phone="9876543212", normalized_phone="9876543212", status=LeadStatus.CONTACTED)
        lsh_a = LeadStatusHistory.objects.create(lead=lead_a, old_status=LeadStatus.NEW, new_status=LeadStatus.CONTACTED)
        LeadStatusHistory.objects.filter(pk=lsh_a.pk).update(created_at=now - timedelta(hours=5))
        # Touch lead.updated_at to now (must NOT fool timestamp comparison)
        Lead.objects.filter(pk=lead_a.pk).update(updated_at=now)
        ingest_or_merge_lead(self._raw_lead("tc_2a", "919876543212", "Interested", status_dt=now - timedelta(hours=1)))
        lead_a.refresh_from_db()
        self.assertEqual(lead_a.status, LeadStatus.INTERESTED)

        # 2b. Newer CRM LeadStatusHistory wins
        lead_b = Lead.objects.create(name="Lead 2B", phone="9876543213", normalized_phone="9876543213", status=LeadStatus.DISCUSSION)
        lsh_b = LeadStatusHistory.objects.create(lead=lead_b, old_status=LeadStatus.NEW, new_status=LeadStatus.DISCUSSION)
        LeadStatusHistory.objects.filter(pk=lsh_b.pk).update(created_at=now - timedelta(minutes=10))
        ingest_or_merge_lead(self._raw_lead("tc_2b", "919876543213", "Contacted", status_dt=now - timedelta(hours=3)))
        lead_b.refresh_from_db()
        self.assertEqual(lead_b.status, LeadStatus.DISCUSSION)

        # 2c. No CRM status history -> TeleCRM wins
        lead_c = Lead.objects.create(name="Lead 2C", phone="9876543214", normalized_phone="9876543214", status=LeadStatus.DISCUSSION)
        ingest_or_merge_lead(self._raw_lead("tc_2c", "919876543214", "Demo Attended", status_dt=now - timedelta(days=10)))
        lead_c.refresh_from_db()
        self.assertEqual(lead_c.status, LeadStatus.DEMO_ATTENDED)

    def test_3_enrolled_is_protected_and_creates_sync_conflict(self):
        now = timezone.now()
        lead = Lead.objects.create(name="Enrolled Lead", phone="9876543215", normalized_phone="9876543215", status=LeadStatus.ENROLLED)
        lsh = LeadStatusHistory.objects.create(lead=lead, old_status=LeadStatus.INTERESTED, new_status=LeadStatus.ENROLLED)
        LeadStatusHistory.objects.filter(pk=lsh.pk).update(created_at=now - timedelta(days=2))

        ingest_or_merge_lead(self._raw_lead("tc_3", "919876543215", "Interested", status_dt=now))
        lead.refresh_from_db()
        self.assertEqual(lead.status, LeadStatus.ENROLLED)
        conflict = SyncConflict.objects.get(lead=lead, status=SyncConflict.STATUS_OPEN)
        self.assertEqual(conflict.crm_status, LeadStatus.ENROLLED)
        self.assertEqual(conflict.telecrm_status, LeadStatus.INTERESTED)
        self.assertEqual(conflict.applied_status, LeadStatus.ENROLLED)

    def test_4_lost_vs_enrolled_becomes_enrolled(self):
        now = timezone.now()
        lead = Lead.objects.create(name="Lost Lead", phone="9876543216", normalized_phone="9876543216", status=LeadStatus.LOST)
        LeadStatusHistory.objects.create(lead=lead, old_status=LeadStatus.NEW, new_status=LeadStatus.LOST)
        ingest_or_merge_lead(self._raw_lead("tc_4", "919876543216", "Won_Velachery", status_dt=now - timedelta(days=1)))
        lead.refresh_from_db()
        self.assertEqual(lead.status, LeadStatus.ENROLLED)

    def test_5_both_sides_edited_between_two_sync_runs(self):
        t0 = timezone.now() - timedelta(hours=6)
        # First sync: both agree on Contacted
        raw1 = self._raw_lead("tc_5", "919876543217", "Call Taken", status_dt=t0)
        lead, mirror, _ = ingest_or_merge_lead(raw1)
        self.assertEqual(lead.status, LeadStatus.CONTACTED)
        self.assertEqual(mirror.last_synced_status, LeadStatus.CONTACTED)

        # Between sync 1 and sync 2: CRM edits to Discussion at t1, TeleCRM edits to Interested at t2 (newer)
        t1 = timezone.now() - timedelta(hours=2)
        t2 = timezone.now() - timedelta(hours=1)
        lead.status = LeadStatus.DISCUSSION
        lead.save(update_fields=["status"])
        lsh_crm = LeadStatusHistory.objects.create(lead=lead, old_status=LeadStatus.CONTACTED, new_status=LeadStatus.DISCUSSION, remarks="[CRM] Edited in CRM")
        LeadStatusHistory.objects.filter(pk=lsh_crm.pk).update(created_at=t1)

        # Second sync: both changed since last_synced_status -> newer TeleCRM wins AND creates SyncConflict
        raw2 = self._raw_lead("tc_5", "919876543217", "Interested", status_dt=t2)
        lead2, mirror2, _ = ingest_or_merge_lead(raw2)
        self.assertEqual(lead2.status, LeadStatus.INTERESTED)
        conflict = SyncConflict.objects.get(lead=lead2, status=SyncConflict.STATUS_OPEN)
        self.assertEqual(conflict.crm_status, LeadStatus.DISCUSSION)
        self.assertEqual(conflict.telecrm_status, LeadStatus.INTERESTED)
        self.assertEqual(conflict.applied_status, LeadStatus.INTERESTED)
        # Timeline preserved both entries
        self.assertGreaterEqual(LeadStatusHistory.objects.filter(lead=lead2).count(), 3)

    def test_6_assignee_active_crm_kept_inactive_replaced(self):
        # Active CRM assignee kept
        lead_a = Lead.objects.create(
            name="Active Assignee", phone="9876543218", normalized_phone="9876543218",
            assigned_telecaller=self.tc_active, current_owner_type="TELECALLER"
        )
        ingest_or_merge_lead(self._raw_lead("tc_6a", "919876543218", "Call Taken", employee="tc_other@test.com"))
        lead_a.refresh_from_db()
        self.assertEqual(lead_a.assigned_telecaller, self.tc_active)

        # Inactive CRM assignee replaced by TeleCRM active assignee
        lead_b = Lead.objects.create(
            name="Inactive Assignee", phone="9876543219", normalized_phone="9876543219",
            assigned_telecaller=self.tc_inactive, current_owner_type="TELECALLER"
        )
        ingest_or_merge_lead(self._raw_lead("tc_6b", "919876543219", "Call Taken", employee="tc_other@test.com"))
        lead_b.refresh_from_db()
        self.assertEqual(lead_b.assigned_telecaller, self.tc_other)

    def test_7_other_fields_fill_blanks_only_and_actions_append_dedupe(self):
        lead = Lead.objects.create(
            name="CRM Real Name", phone="9876543220", normalized_phone="9876543220",
            email="", branch=self.branch_tn
        )
        actions = [{
            "id": "act_call_1",
            "type": "OUTGOING_CALL",
            "creationTimestamp": int(timezone.now().timestamp() * 1000),
            "employeeid": "tc_other@test.com",
            "duration": 45,
            "feedback": "CONNECTED",
            "note": "Discussed course",
            "callRecording": {"filePath": "ent/emp/26112026/919876543220/rec1.mp3"},
        }]
        raw = self._raw_lead("tc_7", "919876543220", "Call Taken", name="TeleCRM Name", email="filled@test.com")
        sync_telecrm_lead_payload(raw, actions)
        # Run second time -> actions deduped, CRM name preserved, blank email filled
        sync_telecrm_lead_payload(raw, actions)

        lead.refresh_from_db()
        self.assertEqual(lead.name, "CRM Real Name")
        self.assertEqual(lead.email, "filled@test.com")
        self.assertEqual(CallHistory.objects.filter(lead=lead).count(), 1)
        ch = CallHistory.objects.get(lead=lead)
        self.assertEqual(ch.telecrm_recording_path, "ent/emp/26112026/919876543220/rec1.mp3")
        self.assertEqual(ch.recording_url, "")
        self.assertEqual(CallRecording.objects.count(), 0)

    def test_8_sync_conflicts_page_rbac_and_resolution(self):
        lead_tn = Lead.objects.create(name="TN Conflict", phone="9876543221", normalized_phone="9876543221", branch=self.branch_tn, status=LeadStatus.ENROLLED)
        lead_vel = Lead.objects.create(name="VEL Conflict", phone="9876543222", normalized_phone="9876543222", branch=self.branch_vel, status=LeadStatus.ENROLLED)
        c_tn = SyncConflict.objects.create(
            lead=lead_tn, crm_status=LeadStatus.ENROLLED, telecrm_status=LeadStatus.INTERESTED,
            applied_status=LeadStatus.ENROLLED, rule_applied="enrolled_protected_crm"
        )
        c_vel = SyncConflict.objects.create(
            lead=lead_vel, crm_status=LeadStatus.ENROLLED, telecrm_status=LeadStatus.LOST,
            applied_status=LeadStatus.ENROLLED, rule_applied="enrolled_protected_crm"
        )

        # Telecaller forbidden
        cli = Client()
        cli.force_login(self.tc_active)
        self.assertEqual(cli.get(reverse("telecrm_sync_conflicts")).status_code, 403)

        # Branch Head T. Nagar sees ONLY T. Nagar conflict
        cli.force_login(self.bh_tn)
        resp_bh = cli.get(reverse("telecrm_sync_conflicts"))
        self.assertEqual(resp_bh.status_code, 200)
        self.assertContains(resp_bh, "TN Conflict")
        self.assertNotContains(resp_bh, "VEL Conflict")

        # Resolve TN conflict with Use TeleCRM -> logs audit + updates lead
        resp_res = cli.post(reverse("telecrm_resolve_conflict", args=[c_tn.id]), {"decision": "use_telecrm"})
        self.assertEqual(resp_res.status_code, 302)
        c_tn.refresh_from_db()
        lead_tn.refresh_from_db()
        self.assertEqual(c_tn.status, SyncConflict.STATUS_USED_TELECRM)
        self.assertEqual(lead_tn.status, LeadStatus.INTERESTED)
        self.assertTrue(Activity.objects.filter(action="TeleCRM Conflict Resolved", object_id=str(lead_tn.id)).exists())

        # Sales Head sees VEL conflict and resolves Keep CRM
        cli.force_login(self.sales_head)
        resp_sh = cli.get(reverse("telecrm_sync_conflicts"))
        self.assertEqual(resp_sh.status_code, 200)
        self.assertContains(resp_sh, "VEL Conflict")
        cli.post(reverse("telecrm_resolve_conflict", args=[c_vel.id]), {"decision": "keep_crm"})
        c_vel.refresh_from_db()
        self.assertEqual(c_vel.status, SyncConflict.STATUS_KEPT_CRM)
