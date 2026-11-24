from datetime import date, datetime, timezone as dt_timezone
from django.test import TestCase

from accounts.models import User, UserRole
from branches.models import Branch
from calls.models import CallDevice, CallEvent
from calls.sync_services import ingest_calls
from leads.models import Lead


class CallSyncCutoffTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.filter(name="Velachery").first() or Branch.objects.create(name="Velachery", status="Active")
        self.telecaller = User.objects.create_user(
            username="caller_cutoff_test",
            email="caller_cutoff@techpanda.test",
            password="testpassword123",
            role=UserRole.TELECALLER,
            branch=self.branch,
        )
        self.device = CallDevice.objects.create(
            user=self.telecaller,
            sync_cutoff_date=date(2026, 11, 20)
        )

    def test_ingest_calls_skips_calls_before_cutoff_date(self):
        """Calls with started_at prior to device.sync_cutoff_date must be skipped."""
        old_call_ts = int(datetime(2026, 11, 15, 14, 30, tzinfo=dt_timezone.utc).timestamp() * 1000)
        fresh_call_ts = int(datetime(2026, 11, 22, 11, 0, tzinfo=dt_timezone.utc).timestamp() * 1000)

        calls_payload = [
            {
                "number": "9876500001",
                "call_type": "incoming",
                "timestamp_ms": old_call_ts,
                "duration_sec": 45,
                "contact_name": "Old Caller"
            },
            {
                "number": "9876500002",
                "call_type": "incoming",
                "timestamp_ms": fresh_call_ts,
                "duration_sec": 30,
                "contact_name": "Fresh Caller"
            }
        ]

        summary = ingest_calls(self.device, calls_payload)
        self.assertEqual(summary["created"], 1)
        self.assertEqual(summary["skipped_cutoff"], 1)
        self.assertEqual(summary["new_leads"], 1)

        # Verify old call was never ingested into CallEvent or Lead
        self.assertFalse(CallEvent.objects.filter(raw_number="9876500001").exists())
        self.assertFalse(Lead.objects.filter(phone="9876500001").exists())

        # Verify fresh call was ingested
        self.assertTrue(CallEvent.objects.filter(raw_number="9876500002").exists())
        self.assertTrue(Lead.objects.filter(phone="9876500002").exists())
