import json
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import User, UserRole
from branches.models import Branch
from fb_leads.models import FacebookAccount, FacebookPage, FacebookLead
from fb_leads.facebook import save_lead, sync_page_leads
from leads.models import Lead


class FacebookSyncCutoffTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.branch = Branch.objects.create(name="T-Nagar", status="Active")
        self.admin = User.objects.create_superuser(
            username="admin_cutoff",
            email="admin_cutoff@techpanda.test",
            password="adminpassword123",
            role=UserRole.ADMIN,
            branch=self.branch,
        )
        self.account = FacebookAccount.objects.create(
            account_name="Techpanda FB",
            access_token="test_token_fb",
            status="CONNECTED"
        )
        self.page = FacebookPage.objects.create(
            account=self.account,
            page_id="page_12345",
            page_name="Techpanda Page",
            branch=self.branch,
            page_access_token="page_token_12345",
            sync_cutoff_date=date(2026, 11, 20),
            status="CONNECTED"
        )

    def test_save_lead_skips_lead_before_cutoff_date(self):
        """Lead created prior to cutoff date must be skipped completely."""
        lead_dict_old = {
            "id": "lead_old_999",
            "created_time": "2026-11-15T10:00:00+0000",
            "field_data": [
                {"name": "full_name", "values": ["Old Lead"]},
                {"name": "phone_number", "values": ["9876543210"]},
            ]
        }
        res, created = save_lead(lead_dict_old, page_id=self.page.page_id, cutoff_date=self.page.sync_cutoff_date)
        self.assertIsNone(res)
        self.assertFalse(created)
        self.assertFalse(FacebookLead.objects.filter(leadgen_id="lead_old_999").exists())
        self.assertFalse(Lead.objects.filter(phone="9876543210").exists())

    def test_save_lead_accepts_lead_on_or_after_cutoff_date(self):
        """Lead created on or after cutoff date must be imported into CRM."""
        lead_dict_new = {
            "id": "lead_new_111",
            "created_time": "2026-11-22T10:00:00+0000",
            "field_data": [
                {"name": "full_name", "values": ["Fresh Lead"]},
                {"name": "phone_number", "values": ["9123456780"]},
            ]
        }
        res, created = save_lead(lead_dict_new, page_id=self.page.page_id, cutoff_date=self.page.sync_cutoff_date)
        self.assertIsNotNone(res)
        self.assertTrue(created)
        self.assertTrue(FacebookLead.objects.filter(leadgen_id="lead_new_111").exists())
        self.assertTrue(Lead.objects.filter(phone="9123456780").exists())

    def test_update_cutoff_date_endpoint_ajax(self):
        """Admin can update cutoff date via AJAX endpoint."""
        self.client.force_login(self.admin)
        url = reverse("fb_leads:fb_page_update_cutoff_date", args=[self.page.id])
        res = self.client.post(
            url,
            {"cutoff_date": "2026-11-25"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["cutoff_date"], "2026-11-25")

        self.page.refresh_from_db()
        self.assertEqual(self.page.sync_cutoff_date, date(2026, 11, 25))

    def test_clear_cutoff_date_endpoint_ajax(self):
        """Clearing cutoff date sets sync_cutoff_date to None."""
        self.client.force_login(self.admin)
        url = reverse("fb_leads:fb_page_update_cutoff_date", args=[self.page.id])
        res = self.client.post(
            url,
            {"cutoff_date": ""},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["cutoff_date"], "")

        self.page.refresh_from_db()
        self.assertIsNone(self.page.sync_cutoff_date)

    @patch("fb_leads.facebook._get")
    def test_sync_page_leads_applies_filtering_and_cutoff(self, mock_get):
        """sync_page_leads passes filtering parameter and skips older leads."""
        mock_get.side_effect = [
            {"data": [{"id": "form_1", "name": "Test Form"}]},  # forms
            {
                "data": [
                    {
                        "id": "lead_old_888",
                        "created_time": "2026-11-10T12:00:00+0000",
                        "field_data": [{"name": "phone_number", "values": ["9998887771"]}]
                    },
                    {
                        "id": "lead_fresh_888",
                        "created_time": "2026-11-23T12:00:00+0000",
                        "field_data": [{"name": "phone_number", "values": ["9998887772"]}]
                    }
                ],
                "paging": {}
            }
        ]

        count = sync_page_leads(self.page.page_id)
        self.assertEqual(count, 1)
        self.assertFalse(FacebookLead.objects.filter(leadgen_id="lead_old_888").exists())
        self.assertTrue(FacebookLead.objects.filter(leadgen_id="lead_fresh_888").exists())
