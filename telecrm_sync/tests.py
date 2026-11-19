from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import MagicMock, patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from accounts.models import UserRole
from activities.models import Activity, Notification
from activities.services import create_notification
from branches.models import Branch
from calls.models import CallHistory, CallOutcome, CallStatus
from chat.models import Conversation, Message
from fb_leads.models import FacebookLead
from leads.models import (
    Lead,
    LeadAssignmentHistory,
    LeadStatus,
    LeadStatusHistory,
)
from products.models import Product
from .client import (
    TeleCRMAuthError,
    TeleCRMClient,
    TeleCRMError,
    TeleCRMRateLimitError,
    TeleCRMServerError,
)
from .mapper import (
    determine_lead_source_and_platform,
    ingest_lead_actions,
    ingest_or_merge_lead,
    is_sync_suppressed,
    normalize_telecrm_phone,
    resolve_branch_from_text,
    resolve_crm_status,
    resolve_telecrm_user,
    suppress_sync_side_effects,
    sync_telecrm_lead_payload,
)
from .models import (
    TeleCRMAction,
    TeleCRMLead,
    TeleCRMStatusMap,
    TeleCRMSyncRun,
    TeleCRMUser,
)

User = get_user_model()


class TeleCRMClientTests(TestCase):
    def setUp(self):
        self.client = TeleCRMClient(token="test_sync_token", enterprise_id="ent_123")
        self.client.INITIAL_BACKOFF_SEC = 0.01
        self.client.MAX_BACKOFF_SEC = 0.02

    @patch("requests.Session.request")
    def test_count_leads_success(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"total_count": 91420}'
        mock_resp.json.return_value = {"total_count": 91420}
        mock_request.return_value = mock_resp

        count = self.client.count_leads()
        self.assertEqual(count, 91420)
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs["params"], {"onlyCount": "true"})
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_sync_token")

    @patch("requests.Session.request")
    def test_list_leads_success(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"data": [{"id": "lead_1", "fields": {"name": "Test"}}, {"id": "lead_2"}]}'
        mock_resp.json.return_value = {
            "data": [{"id": "lead_1", "fields": {"name": "Test"}}, {"id": "lead_2"}]
        }
        mock_request.return_value = mock_resp

        leads = self.client.list_leads(skip=10, limit=50)
        self.assertEqual(len(leads), 2)
        self.assertEqual(leads[0]["id"], "lead_1")
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs["params"], {"skip": 10, "limit": 50})

    @patch("requests.Session.request")
    def test_list_leads_active_between(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"data": [{"id": "lead_active"}], "total_count": 1}'
        mock_resp.json.return_value = {"data": [{"id": "lead_active"}], "total_count": 1}
        mock_request.return_value = mock_resp

        start_dt = datetime(2026, 11, 19, 10, 0, tzinfo=dt_timezone.utc)
        end_dt = datetime(2026, 11, 19, 11, 0, tzinfo=dt_timezone.utc)
        leads, count = self.client.list_leads_active_between(start_dt, end_dt, skip=0, limit=100)

        self.assertEqual(count, 1)
        self.assertEqual(len(leads), 1)
        args, kwargs = mock_request.call_args
        self.assertIn("actions", kwargs["json"])
        self.assertIn("performed_at", kwargs["json"]["actions"])

    @patch("requests.Session.request")
    def test_get_lead_actions(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"data": [{"id": "act_1", "type": "OUTGOING_CALL"}], "total_count": 1}'
        mock_resp.json.return_value = {
            "data": [{"id": "act_1", "type": "OUTGOING_CALL"}],
            "total_count": 1
        }
        mock_request.return_value = mock_resp

        actions, total = self.client.get_lead_actions("lead_123", skip=0, limit=20)
        self.assertEqual(total, 1)
        self.assertEqual(actions[0]["type"], "OUTGOING_CALL")

    @patch("requests.Session.request")
    def test_get_team_members(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"data": [{"uid": "u1", "email": "agent@itechpanda.com"}]}'
        mock_resp.json.return_value = {
            "data": [{"uid": "u1", "email": "agent@itechpanda.com"}]
        }
        mock_request.return_value = mock_resp

        members = self.client.get_team_members()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]["email"], "agent@itechpanda.com")

    @patch("requests.Session.request")
    def test_get_lead_stage_pipeline(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"statuses": [{"id": "1", "label": "Fresh"}]}'
        mock_resp.json.return_value = {"statuses": [{"id": "1", "label": "Fresh"}]}
        mock_request.return_value = mock_resp

        pipeline = self.client.get_lead_stage_pipeline()
        self.assertIn("statuses", pipeline)
        self.assertEqual(pipeline["statuses"][0]["label"], "Fresh")

    @patch("requests.Session.request")
    def test_auth_error_non_retryable(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized - invalid sync token"
        mock_request.return_value = mock_resp

        with self.assertRaises(TeleCRMAuthError):
            self.client.count_leads()
        self.assertEqual(mock_request.call_count, 1)

    @patch("requests.Session.request")
    def test_retry_on_server_error(self, mock_request):
        mock_resp_500 = MagicMock()
        mock_resp_500.status_code = 500
        mock_resp_500.text = "Internal Server Error"

        mock_resp_200 = MagicMock()
        mock_resp_200.status_code = 200
        mock_resp_200.text = '{"total_count": 50}'
        mock_resp_200.json.return_value = {"total_count": 50}

        mock_request.side_effect = [mock_resp_500, mock_resp_200]

        count = self.client.count_leads()
        self.assertEqual(count, 50)
        self.assertEqual(mock_request.call_count, 2)


class TeleCRMMapperHelperTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch_tnagar = Branch.objects.get_or_create(name="T. Nagar")[0]
        cls.branch_annanagar = Branch.objects.get_or_create(name="Anna Nagar")[0]
        cls.telecaller = User.objects.create_user(
            username="test_telecaller",
            email="telecaller@itechpanda.com",
            role=UserRole.TELECALLER
        )
        cls.counselor = User.objects.create_user(
            username="test_counselor",
            email="counselor@itechpanda.com",
            role=UserRole.COUNSELOR
        )

    def test_normalize_telecrm_phone(self):
        self.assertEqual(normalize_telecrm_phone("+919876543210"), "9876543210")
        self.assertEqual(normalize_telecrm_phone("919876543210"), "9876543210")
        self.assertEqual(normalize_telecrm_phone("09876543210"), "9876543210")
        self.assertEqual(normalize_telecrm_phone("9876543210"), "9876543210")
        self.assertEqual(normalize_telecrm_phone("+14155552671"), "+14155552671")
        self.assertEqual(normalize_telecrm_phone("", "lead_xyz"), "NoPhone-lead_xyz")
        self.assertEqual(normalize_telecrm_phone("null", "lead_xyz"), "NoPhone-lead_xyz")

    def test_resolve_telecrm_user(self):
        u = resolve_telecrm_user("telecaller@itechpanda.com")
        self.assertEqual(u, self.telecaller)

        TeleCRMUser.objects.create(
            uid="uid_counselor_99",
            email="counselor@itechpanda.com",
            name="Counselor Person",
            crm_user=self.counselor
        )
        u2 = resolve_telecrm_user("uid_counselor_99")
        self.assertEqual(u2, self.counselor)

        self.assertIsNone(resolve_telecrm_user("__telecrm"))

    def test_resolve_crm_status(self):
        self.assertEqual(resolve_crm_status("Fresh"), LeadStatus.NEW)
        self.assertEqual(resolve_crm_status("Interested"), LeadStatus.INTERESTED)
        self.assertEqual(resolve_crm_status("Call not picked_1"), LeadStatus.NO_ANSWER)
        self.assertEqual(resolve_crm_status("RNR"), LeadStatus.NO_ANSWER)
        self.assertEqual(resolve_crm_status("Busy"), LeadStatus.BUSY)
        self.assertEqual(resolve_crm_status("Switched off"), LeadStatus.SWITCHED_OFF)
        self.assertEqual(resolve_crm_status("Converted"), LeadStatus.ENROLLED)
        self.assertEqual(resolve_crm_status("Enrolled"), LeadStatus.ENROLLED)
        self.assertEqual(resolve_crm_status("UnknownStatus"), LeadStatus.NEW)

    def test_determine_lead_source_and_platform(self):
        fb_actions = [
            {
                "id": "act_fb",
                "type": "FACEBOOK",
                "creationTimestamp": 1000,
                "pageName": "Techpanda Anna Nagar",
            },
            {
                "id": "act_call",
                "type": "OUTGOING_CALL",
                "creationTimestamp": 2000,
            }
        ]
        src, plat, inf_branch = determine_lead_source_and_platform(fb_actions)
        self.assertEqual(src, "Facebook")
        self.assertEqual(plat, "facebook")
        self.assertEqual(inf_branch, "Anna Nagar")

        wa_actions = [
            {
                "id": "act_wa",
                "type": "INCOMING_WHATSAPP_MSG",
                "creationTimestamp": 1000,
                "referralMsg": {"sourceUrl": "https://www.instagram.com/p/123"},
            }
        ]
        src, plat, inf_branch = determine_lead_source_and_platform(wa_actions)
        self.assertEqual(src, "Meta Ads")
        self.assertEqual(plat, "instagram")

        src_def, plat_def, _ = determine_lead_source_and_platform([])
        self.assertEqual(src_def, "TeleCRM")
        self.assertEqual(plat_def, "other")


class TeleCRMLeadIngestionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch_tnagar = Branch.objects.get_or_create(name="T. Nagar")[0]
        cls.branch_annanagar = Branch.objects.get_or_create(name="Anna Nagar")[0]
        cls.telecaller = User.objects.create_user(
            username="tc_agent",
            email="tc@itechpanda.com",
            role=UserRole.TELECALLER
        )
        cls.counselor = User.objects.create_user(
            username="co_agent",
            email="co@itechpanda.com",
            role=UserRole.COUNSELOR
        )

    def test_create_new_lead_with_rating_zero_and_branch_inference(self):
        raw_lead = {
            "id": "tc_lead_new_1",
            "employeeid": "tc@itechpanda.com",
            "status": "Fresh",
            "rating": 0,
            "fields": {
                "name": "Arun Kumar",
                "phone": "+919876500001",
                "email_1": "arun@example.com",
                "courses": "full_stack_development",
                "created_on": 1700000000000,
                "modified_on": 1700000000000,
            }
        }
        actions = [
            {
                "id": "act_fb_1",
                "type": "FACEBOOK",
                "creationTimestamp": 1700000000000,
                "pageName": "Techpanda Anna Nagar",
            }
        ]

        lead, tc_mirror, created = ingest_or_merge_lead(raw_lead, actions)
        self.assertTrue(created)
        self.assertEqual(lead.name, "Arun Kumar")
        self.assertEqual(lead.normalized_phone, "9876500001")
        self.assertEqual(lead.email, "arun@example.com")
        self.assertEqual(lead.status, LeadStatus.NEW)
        # Rating 0 must be empty / None, NOT 1
        self.assertIsNone(lead.rating)
        self.assertEqual(lead.custom_fields.get("telecrm_rating"), 0)
        # Branch inferred from Facebook pageName because base_branch was empty
        self.assertEqual(lead.branch, self.branch_annanagar)
        # Assignee role TELECALLER -> assigned_telecaller set
        self.assertEqual(lead.assigned_telecaller, self.telecaller)
        self.assertIsNone(lead.assigned_counselor)
        self.assertEqual(lead.current_owner_type, "TELECALLER")
        self.assertEqual(lead.assignment_status, "Assigned")

    def test_create_new_lead_with_counselor_assignment(self):
        raw_lead = {
            "id": "tc_lead_counselor_1",
            "employeeid": "co@itechpanda.com",
            "status": "Interested",
            "rating": 4,
            "fields": {
                "name": "Kavitha S",
                "phone": "9876500002",
                "created_on": 1700000000000,
            }
        }
        lead, _, created = ingest_or_merge_lead(raw_lead)
        self.assertTrue(created)
        self.assertEqual(lead.rating, 4)
        self.assertEqual(lead.assigned_counselor, self.counselor)
        self.assertIsNone(lead.assigned_telecaller)
        self.assertEqual(lead.current_owner_type, "COUNSELOR")

    def test_merge_existing_lead_terminal_status_protection(self):
        existing = Lead.objects.create(
            name="Existing Student",
            phone="9876500003",
            normalized_phone="9876500003",
            email="student@example.com",
            status=LeadStatus.ENROLLED,
            branch=self.branch_tnagar
        )

        raw_lead = {
            "id": "tc_lead_merge_1",
            "status": "Lost",
            "fields": {
                "name": "Updated Name",
                "phone": "9876500003",
                "email_1": "",
            }
        }
        lead, _, created = ingest_or_merge_lead(raw_lead)
        self.assertFalse(created)
        self.assertEqual(lead.id, existing.id)
        # Terminal status ENROLLED must NOT be downgraded to Lost
        self.assertEqual(lead.status, LeadStatus.ENROLLED)
        # Existing email must not be overwritten by empty email
        self.assertEqual(lead.email, "student@example.com")

    def test_merge_replaces_placeholder_name(self):
        existing = Lead.objects.create(
            name="Lead 9876500004",
            phone="9876500004",
            normalized_phone="9876500004",
            status=LeadStatus.NEW
        )

        raw_lead = {
            "id": "tc_lead_name_replace",
            "fields": {
                "name": "Real Prospect Name",
                "phone": "9876500004",
            }
        }
        lead, _, created = ingest_or_merge_lead(raw_lead)
        self.assertFalse(created)
        self.assertEqual(lead.name, "Real Prospect Name")


class TeleCRMActionIngestionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.telecaller = User.objects.create_user(
            username="tc_call_agent",
            email="call_agent@itechpanda.com",
            role=UserRole.TELECALLER
        )
        cls.lead = Lead.objects.create(
            name="Call Test Lead",
            phone="9876500005",
            normalized_phone="9876500005",
            status=LeadStatus.NEW
        )
        cls.tc_lead = TeleCRMLead.objects.create(
            telecrm_id="tc_lead_act_test",
            phone="9876500005",
            crm_lead=cls.lead
        )

    def test_call_sync_deduplication(self):
        call_time = datetime(2026, 11, 19, 10, 30, tzinfo=dt_timezone.utc)
        call_time_ms = int(call_time.timestamp() * 1000)

        existing_call = CallHistory.objects.create(
            lead=self.lead,
            caller=self.telecaller,
            call_started_at=call_time,
            duration=45,
            call_status=CallStatus.CONNECTED,
            call_outcome=CallOutcome.INTERESTED,
            notes="Recording from Call Sync Android App",
            recording_url="local_recordings/rec_001.mp3"
        )

        # TeleCRM action arriving with start time 20 seconds later (+20s) and same duration (45s)
        telecrm_call_action = [
            {
                "id": "tc_act_call_duplicate",
                "type": "OUTGOING_CALL",
                "creationTimestamp": call_time_ms + 20000,
                "duration": 45,
                "feedback": "CONNECTED",
                "note": "TeleCRM duplicate call",
                "employeeid": "call_agent@itechpanda.com"
            }
        ]

        mapped_count = ingest_lead_actions(self.lead, self.tc_lead, telecrm_call_action)
        self.assertEqual(mapped_count, 1)

        # Verify only 1 CallHistory record exists in total (no duplicate created!)
        self.assertEqual(CallHistory.objects.filter(lead=self.lead).count(), 1)
        self.assertEqual(CallHistory.objects.first().id, existing_call.id)
        act_rec = TeleCRMAction.objects.get(telecrm_id="tc_act_call_duplicate")
        self.assertEqual(act_rec.crm_object_type, "CallHistory")
        self.assertEqual(act_rec.crm_object_id, str(existing_call.id))

    def test_notes_route_to_activity_only(self):
        note_actions = [
            {
                "id": "tc_act_note_user",
                "type": "USER_NOTE",
                "creationTimestamp": 1700000000000,
                "text": "User manual note content",
                "employeeid": "call_agent@itechpanda.com"
            },
            {
                "id": "tc_act_note_system",
                "type": "SYSTEM_NOTE",
                "creationTimestamp": 1700000005000,
                "text": "System notification content",
                "employeeid": "__telecrm"
            }
        ]

        self.lead.notes = ""
        self.lead.save()

        mapped_count = ingest_lead_actions(self.lead, self.tc_lead, note_actions)
        self.assertEqual(mapped_count, 2)

        self.lead.refresh_from_db()
        self.assertEqual(self.lead.notes, "")

        activities = Activity.objects.filter(object_id=str(self.lead.id))
        self.assertEqual(activities.count(), 2)

        user_act = activities.filter(action="TeleCRM Note").first()
        self.assertIsNotNone(user_act)
        self.assertEqual(user_act.user, self.telecaller)
        self.assertEqual(user_act.description, "User manual note content")

        sys_act = activities.filter(action="TeleCRM System Note").first()
        self.assertIsNotNone(sys_act)
        self.assertIsNone(sys_act.user)
        self.assertEqual(sys_act.description, "System notification content")

    def test_status_change_and_assignment_actions(self):
        actions = [
            {
                "id": "tc_act_status_1",
                "type": "STATUS_CHANGE",
                "creationTimestamp": 1700000010000,
                "fromStatusid": "1",
                "toStatusid": "3",
                "employeeid": "call_agent@itechpanda.com"
            },
            {
                "id": "tc_act_assign_1",
                "type": "LEAD_ASSIGNMENT",
                "creationTimestamp": 1700000015000,
                "assignedto": "call_agent@itechpanda.com"
            }
        ]
        mapped_count = ingest_lead_actions(self.lead, self.tc_lead, actions)
        self.assertEqual(mapped_count, 2)

        status_history = LeadStatusHistory.objects.filter(lead=self.lead)
        self.assertEqual(status_history.count(), 1)
        self.assertEqual(status_history.first().new_status, LeadStatus.INTERESTED)

        assign_history = LeadAssignmentHistory.objects.filter(lead=self.lead)
        self.assertEqual(assign_history.count(), 1)
        self.assertEqual(assign_history.first().to_user, self.telecaller)

    def test_idempotent_reexecution(self):
        actions = [
            {
                "id": "tc_act_idempotent_test",
                "type": "SYSTEM_NOTE",
                "creationTimestamp": 1700000020000,
                "text": "Idempotent note"
            }
        ]
        count1 = ingest_lead_actions(self.lead, self.tc_lead, actions)
        self.assertEqual(count1, 1)

        count2 = ingest_lead_actions(self.lead, self.tc_lead, actions)
        self.assertEqual(count2, 0)
        self.assertEqual(Activity.objects.filter(description="Idempotent note").count(), 1)


class TeleCRMSideEffectSuppressionTests(TestCase):
    def test_side_effect_suppression_prevents_notifications(self):
        user = User.objects.create_user(username="notify_user", email="notify@itechpanda.com")

        # Outside suppression: Notification is created
        self.assertFalse(is_sync_suppressed())
        n1 = create_notification(user, "Normal alert", "Normal body")
        self.assertIsNotNone(n1)
        self.assertEqual(Notification.objects.filter(recipient=user).count(), 1)

        # Inside suppression: Notification is completely suppressed
        with suppress_sync_side_effects():
            self.assertTrue(is_sync_suppressed())
            n2 = create_notification(user, "Suppressed alert", "Suppressed body")
            self.assertIsNone(n2)
            self.assertEqual(Notification.objects.filter(recipient=user).count(), 1)

        # Outside suppression again: Flag reverts to False
        self.assertFalse(is_sync_suppressed())


class TeleCRMImportCommandTests(TestCase):
    def test_missing_token_raises_command_error(self):
        from io import StringIO
        from django.core.management import call_command
        from django.core.management.base import CommandError

        out = StringIO()
        with patch("telecrm_sync.client.settings.TELECRM_TOKEN", ""):
            with patch("telecrm_sync.management.commands.telecrm_import.settings.TELECRM_TOKEN", ""):
                with self.assertRaises(CommandError):
                    call_command("telecrm_import", stdout=out)

    @patch("telecrm_sync.management.commands.telecrm_import.TeleCRMClient")
    def test_import_command_end_to_end_mocked(self, mock_client_cls):
        from io import StringIO
        from django.core.management import call_command

        mock_client = MagicMock()
        mock_client.token = "mock_sync_token"
        mock_client.enterprise_id = "mock_enterprise"
        mock_client.count_leads.return_value = 2
        mock_client.get_team_members.return_value = [
            {"uid": "uid_agent_1", "email": "agent1@itechpanda.com", "name": "Agent One"}
        ]
        mock_client.get_lead_stage_pipeline.return_value = {
            "statuses": [{"id": "1", "label": "Fresh"}]
        }
        mock_client.list_leads.return_value = [
            {
                "id": "tc_cmd_lead_1",
                "employeeid": "agent1@itechpanda.com",
                "status": "Fresh",
                "rating": 0,
                "fields": {
                    "name": "Command Test Lead 1",
                    "phone": "9876543211",
                    "created_on": 1700000000000,
                }
            },
            {
                "id": "tc_cmd_lead_2",
                "employeeid": "agent1@itechpanda.com",
                "status": "Interested",
                "rating": 5,
                "fields": {
                    "name": "Command Test Lead 2",
                    "phone": "9876543212",
                    "created_on": 1700000010000,
                }
            }
        ]
        mock_client.get_lead_actions.side_effect = [
            ([{"id": "cmd_act_1", "type": "USER_NOTE", "creationTimestamp": 1700000000000, "text": "Note 1"}], 1),
            ([{"id": "cmd_act_2", "type": "USER_NOTE", "creationTimestamp": 1700000010000, "text": "Note 2"}], 1),
        ]
        mock_client_cls.return_value = mock_client

        out = StringIO()
        call_command(
            "telecrm_import",
            "--max", 2,
            "--token", "mock_token",
            "--workers", 1,
            stdout=out
        )

        output = out.getvalue()
        self.assertIn("TeleCRM Import Completed Successfully", output)
        self.assertEqual(Lead.objects.filter(phone__in=["9876543211", "9876543212"]).count(), 2)
        self.assertEqual(TeleCRMLead.objects.count(), 2)
        self.assertEqual(TeleCRMAction.objects.count(), 2)

        sync_run = TeleCRMSyncRun.objects.filter(kind="import").first()
        self.assertIsNotNone(sync_run)
        self.assertEqual(sync_run.status, "COMPLETED")
        self.assertEqual(sync_run.leads_seen, 2)
        self.assertEqual(sync_run.leads_created, 2)


class TeleCRMSyncCommandTests(TestCase):
    def test_disabled_sync_is_noop(self):
        from io import StringIO
        from django.core.management import call_command

        out = StringIO()
        with patch.object(settings, "TELECRM_SYNC_ENABLED", False):
            call_command("telecrm_sync", stdout=out)

        self.assertIn("TELECRM_SYNC_ENABLED is False", out.getvalue())
        self.assertEqual(TeleCRMSyncRun.objects.filter(kind="sync").count(), 0)

    def test_active_lock_prevents_concurrent_runs(self):
        from io import StringIO
        from django.core.management import call_command

        # Create active running task
        TeleCRMSyncRun.objects.create(
            kind="sync",
            status="RUNNING",
            started_at=timezone.now()
        )

        out = StringIO()
        call_command("telecrm_sync", "--force", stdout=out)
        self.assertIn("Another TeleCRM sync task", out.getvalue())
        # No second run was created
        self.assertEqual(TeleCRMSyncRun.objects.filter(kind="sync").count(), 1)

    @patch("telecrm_sync.management.commands.telecrm_sync.TeleCRMClient")
    def test_incremental_sync_end_to_end_mocked(self, mock_client_cls):
        from io import StringIO
        from django.core.management import call_command

        mock_client = MagicMock()
        mock_client.token = "mock_sync_token"
        mock_client.enterprise_id = "mock_enterprise"

        # Discover 1 new lead
        mock_client.list_leads.return_value = [
            {
                "id": "tc_sync_lead_1",
                "employeeid": "agent_sync@itechpanda.com",
                "status": "Fresh",
                "rating": 3,
                "fields": {
                    "name": "Sync Lead One",
                    "phone": "9876543299",
                    "created_on": 1700000000000,
                }
            }
        ]
        # Active in window: none
        mock_client.list_leads_active_between.return_value = ([], 0)

        # 1 new action
        mock_client.get_lead_actions.return_value = (
            [{"id": "sync_act_1", "type": "USER_NOTE", "creationTimestamp": 1700000000000, "text": "Sync note"}],
            1
        )
        mock_client_cls.return_value = mock_client

        out = StringIO()
        call_command("telecrm_sync", "--force", stdout=out)
        output = out.getvalue()

        self.assertIn("COMPLETED", output)
        self.assertEqual(Lead.objects.filter(phone="9876543299").count(), 1)
        self.assertEqual(TeleCRMLead.objects.filter(telecrm_id="tc_sync_lead_1").count(), 1)
        self.assertEqual(TeleCRMAction.objects.filter(telecrm_id="sync_act_1").count(), 1)

        run = TeleCRMSyncRun.objects.filter(kind="sync", status="COMPLETED").first()
        self.assertIsNotNone(run)
        self.assertEqual(run.leads_created, 1)


class TeleCRMPhase5UITests(TestCase):
    """
    Tests for Phase 5 UI Integration:
    - Admin sync dashboard accessibility and metrics rendering
    - Immediate sync trigger endpoint
    - Status mapping & User mapping update endpoints
    - Lead detail view TeleCRM timeline context integration
    - Lead list filtering by source=TeleCRM
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_ui_test",
            email="admin_ui@itechpanda.com",
            password="testpassword123",
            role=UserRole.ADMIN,
        )
        self.telecaller = User.objects.create_user(
            username="telecaller_ui_test",
            email="tc_ui@itechpanda.com",
            password="testpassword123",
            role=UserRole.TELECALLER,
        )
        self.branch, _ = Branch.objects.get_or_create(name="T. Nagar")
        self.lead = Lead.objects.create(
            name="UI Test Lead",
            phone="9876543201",
            source="TeleCRM",
            branch=self.branch,
            status=LeadStatus.NEW,
        )
        self.tc_lead = TeleCRMLead.objects.create(
            telecrm_id="tc_lead_ui_999",
            crm_lead=self.lead,
            phone="9876543201",
            raw={"status": "Fresh"},
            history_fetched=True,
        )
        self.tc_act = TeleCRMAction.objects.create(
            telecrm_id="tc_act_ui_888",
            lead=self.tc_lead,
            type="CALL",
            occurred_at=timezone.now(),
            employee_uid="agent_ui@itechpanda.com",
            raw={"duration": "45s", "notes": "Interested in Python Full Stack"},
            crm_object_type="CallHistory",
            crm_object_id="123",
            mapped_ok=True,
        )

    def test_admin_sync_dashboard_access(self):
        from django.urls import reverse

        # Anonymous -> redirected
        resp = self.client.get(reverse("admin_telecrm_sync_dashboard"))
        self.assertEqual(resp.status_code, 302)

        # Telecaller -> forbidden or redirected
        self.client.force_login(self.telecaller)
        resp = self.client.get(reverse("admin_telecrm_sync_dashboard"))
        self.assertIn(resp.status_code, [302, 403])

        # Admin -> 200 OK
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("admin_telecrm_sync_dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "TeleCRM Integration")

    @patch("telecrm_sync.views.call_command")
    def test_admin_run_sync_now_post(self, mock_call_command):
        from django.urls import reverse

        self.client.force_login(self.admin)
        resp = self.client.post(reverse("admin_telecrm_run_sync_now"))
        self.assertEqual(resp.status_code, 302)
        mock_call_command.assert_called_once()
        self.assertEqual(mock_call_command.call_args[0][0], "telecrm_sync")
        self.assertTrue(mock_call_command.call_args[1].get("force"))

    def test_update_status_map_endpoint(self):
        from django.urls import reverse

        status_obj = TeleCRMStatusMap.objects.create(
            telecrm_status_name="Prospect",
            crm_status=LeadStatus.NEW,
        )
        self.client.force_login(self.admin)
        resp = self.client.post(
            reverse("admin_telecrm_update_status_map"),
            {"mapping_id": status_obj.id, "crm_status": LeadStatus.INTERESTED},
        )
        self.assertEqual(resp.status_code, 302)
        status_obj.refresh_from_db()
        self.assertEqual(status_obj.crm_status, LeadStatus.INTERESTED)

    def test_update_user_map_endpoint(self):
        from django.urls import reverse

        tc_user = TeleCRMUser.objects.create(
            uid="uid_new_123",
            email="new_agent@itechpanda.com",
            name="New Agent",
        )
        self.client.force_login(self.admin)
        resp = self.client.post(
            reverse("admin_telecrm_update_user_map"),
            {"mapping_id": tc_user.id, "crm_user_id": self.telecaller.id},
        )
        self.assertEqual(resp.status_code, 302)
        tc_user.refresh_from_db()
        self.assertEqual(tc_user.crm_user, self.telecaller)

    def test_lead_detail_context_includes_telecrm(self):
        from leads.detail_service import build_lead_detail_context

        ctx = build_lead_detail_context(self.lead, user=self.admin)
        self.assertIsNotNone(ctx.get("telecrm_mirror"))
        self.assertEqual(ctx["telecrm_mirror"].telecrm_id, "tc_lead_ui_999")
        self.assertEqual(len(ctx["telecrm_actions"]), 1)
        self.assertEqual(ctx["telecrm_actions"][0].telecrm_id, "tc_act_ui_888")

    def test_lead_list_source_filtering(self):
        from django.urls import reverse

        Lead.objects.create(
            name="Walkin Lead",
            phone="9876543202",
            source="Walk-in",
            branch=self.branch,
            status=LeadStatus.NEW,
        )
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("admin_leads_list") + "?source=TeleCRM")
        self.assertEqual(resp.status_code, 200)
        leads = resp.context["page_obj"]
        self.assertTrue(any(l.phone == "9876543201" for l in leads))
        self.assertFalse(any(l.phone == "9876543202" for l in leads))



