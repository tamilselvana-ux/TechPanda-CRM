import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import UserRole
from branches.models import Branch
from leads.models import Lead, LeadStatus, LeadStatusHistory
from calls.models import CallHistory
from activities.models import Activity
from telecrm_sync.models import (
    TeleCRMLead, TeleCRMAction, TeleCRMUser, TeleCRMStatusMap
)
from telecrm_sync.mapper import (
    resolve_telecrm_user,
    resolve_crm_status,
    sync_and_provision_telecrm_team,
    build_and_save_uid_mappings,
    ingest_lead_actions,
    remap_telecrm_history_and_assignees,
    DEFAULT_STATUS_MAP
)
from leads.detail_service import build_lead_detail_context

User = get_user_model()


class TeleCRMHistorySyncTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.branch_tn, _ = Branch.objects.get_or_create(name="T. Nagar")
        self.branch_vel, _ = Branch.objects.get_or_create(name="Velachery")
        self.admin_user = User.objects.create_superuser(
            username="admin_sync_test",
            email="admin_sync@example.com",
            password="testpassword123"
        )

    def test_team_members_provisioning_and_role_mapping(self):
        sample_members = [
            {
                "name": "Keerthana_AN",
                "email": "keerthana.test@itechpanda.com",
                "phone_number": "919876543210",
                "permission_template_name": "Telecaller",
            },
            {
                "name": "Karthik_TN",
                "email": "karthik.test@itechpanda.com",
                "phone_number": "919876543211",
                "permission_template_name": "Senior Counselor",
            },
            {
                "name": "Suresh_VEL",
                "email": "suresh.test@itechpanda.com",
                "phone_number": "919876543212",
                "permission_template_name": "Manager",
            }
        ]
        user_dict = sync_and_provision_telecrm_team(sample_members)
        self.assertEqual(len(user_dict), 3)

        u1 = User.objects.get(email="keerthana.test@itechpanda.com")
        self.assertEqual(u1.role, UserRole.TELECALLER)
        self.assertEqual(u1.first_name, "Keerthana")

        u2 = User.objects.get(email="karthik.test@itechpanda.com")
        self.assertEqual(u2.role, UserRole.COUNSELOR)
        self.assertEqual(u2.branch, self.branch_tn)

        u3 = User.objects.get(email="suresh.test@itechpanda.com")
        self.assertEqual(u3.role, UserRole.BRANCH_HEAD)
        self.assertEqual(u3.branch, self.branch_vel)

    def test_uid_to_user_resolution(self):
        crm_user = User.objects.create_user(
            username="priya_caller",
            email="priya.caller@itechpanda.com",
            role=UserRole.TELECALLER
        )
        fake_uid = "AbCdEfGhIjKlMnOpQrStUvWxYz12"
        TeleCRMUser.objects.create(
            uid=fake_uid,
            email=crm_user.email,
            name="Priya_TN",
            crm_user=crm_user
        )

        resolved_by_uid = resolve_telecrm_user(fake_uid)
        self.assertEqual(resolved_by_uid, crm_user)

        resolved_by_email = resolve_telecrm_user("priya.caller@itechpanda.com")
        self.assertEqual(resolved_by_email, crm_user)

    def test_status_pipeline_mapping_coverage(self):
        for stage_id, expected_status in DEFAULT_STATUS_MAP.items():
            resolved = resolve_crm_status("", status_id=stage_id)
            self.assertEqual(resolved, expected_status, f"Stage {stage_id} did not map to {expected_status}")

        self.assertEqual(resolve_crm_status("Won_Online Course"), LeadStatus.ENROLLED)
        self.assertEqual(resolve_crm_status("Center Visited"), LeadStatus.VISITED)
        self.assertEqual(resolve_crm_status("Call Not Picked"), LeadStatus.NO_ANSWER)
        self.assertEqual(resolve_crm_status("Call Not Connected"), LeadStatus.SWITCHED_OFF)

    def test_historical_timestamp_preservation_on_activity_and_status(self):
        crm_user = User.objects.create_user(
            username="ragul_test",
            email="ragul.test@itechpanda.com",
            role=UserRole.TELECALLER
        )
        lead = Lead.objects.create(
            name="Test Lead",
            phone="9876543210",
            status=LeadStatus.NEW
        )
        tl = TeleCRMLead.objects.create(
            telecrm_id="test_telecrm_lead_123",
            crm_lead=lead,
            raw={}
        )

        past_time_note = timezone.now() - datetime.timedelta(days=90)
        past_time_call = timezone.now() - datetime.timedelta(days=85)
        past_time_status = timezone.now() - datetime.timedelta(days=80)

        raw_note = {
            "id": "act_note_1",
            "type": "USER_NOTE",
            "creationTimestamp": int(past_time_note.timestamp() * 1000),
            "employeeid": "fake_ragul_uid",
            "text": "Client requested syllabus details"
        }
        raw_call = {
            "id": "act_call_1",
            "type": "OUTGOING_CALL",
            "creationTimestamp": int(past_time_call.timestamp() * 1000),
            "employeeid": "fake_ragul_uid",
            "duration": 145,
            "feedback": "CONNECTED",
            "callRecording": {"filePath": "https://telecrm.in/rec/test.mp3"}
        }
        raw_status = {
            "id": "act_status_1",
            "type": "STATUS_CHANGE",
            "creationTimestamp": int(past_time_status.timestamp() * 1000),
            "employeeid": "fake_ragul_uid",
            "fromStatusid": 1,
            "toStatusid": 4
        }

        TeleCRMUser.objects.create(
            uid="fake_ragul_uid",
            email=crm_user.email,
            name="Ragul",
            crm_user=crm_user
        )

        mapped_count = ingest_lead_actions(lead, tl, [raw_note, raw_call, raw_status])
        self.assertEqual(mapped_count, 3)

        act = Activity.objects.filter(object_type="Lead", object_id=str(lead.pk)).first()
        self.assertIsNotNone(act)
        self.assertEqual(act.user, crm_user)
        self.assertAlmostEqual(act.timestamp.timestamp(), past_time_note.timestamp(), delta=2)

        call = CallHistory.objects.filter(lead=lead).first()
        self.assertIsNotNone(call)
        self.assertEqual(call.caller, crm_user)
        self.assertEqual(call.telecaller, crm_user)
        self.assertEqual(call.duration, 145)
        self.assertEqual(call.recording_url, "https://telecrm.in/rec/test.mp3")
        self.assertAlmostEqual(call.created_at.timestamp(), past_time_call.timestamp(), delta=2)

        sh = LeadStatusHistory.objects.filter(lead=lead).first()
        self.assertIsNotNone(sh)
        self.assertEqual(sh.changed_by, crm_user)
        self.assertEqual(sh.old_status, LeadStatus.NEW)
        self.assertEqual(sh.new_status, LeadStatus.INTERESTED)
        self.assertAlmostEqual(sh.created_at.timestamp(), past_time_status.timestamp(), delta=2)

    def test_lead_detail_context_timeline_includes_activities(self):
        lead = Lead.objects.create(
            name="Timeline Lead",
            phone="9876543211",
            status=LeadStatus.CONTACTED
        )
        Activity.objects.create(
            user=self.admin_user,
            action="TeleCRM Note",
            description="Discussed pricing options",
            object_type="Lead",
            object_id=str(lead.pk)
        )
        CallHistory.objects.create(
            lead=lead,
            caller=self.admin_user,
            duration=30,
            call_outcome="Connected"
        )
        LeadStatusHistory.objects.create(
            lead=lead,
            changed_by=self.admin_user,
            old_status=LeadStatus.NEW,
            new_status=LeadStatus.CONTACTED
        )

        context = build_lead_detail_context(lead, self.admin_user)
        self.assertIn("activities", context)
        self.assertEqual(len(context["activities"]), 1)
        self.assertEqual(context["timeline_count"], 3)
