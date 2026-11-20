from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, UserRole
from branches.models import Branch
from chat.models import BusinessAccount


class WhatsAppBranchCreationTests(TestCase):
    """
    Test suite verifying that adding a new WhatsApp Business number requires
    and assigns a target CRM Branch.
    """

    def setUp(self):
        self.client = Client()
        self.branch_tn, _ = Branch.objects.get_or_create(name="T. Nagar", defaults={"status": "Active"})
        self.branch_vel, _ = Branch.objects.get_or_create(name="Velachery", defaults={"status": "Active"})

        self.admin = User.objects.create_superuser(
            username="admin_wa_branch",
            email="admin_wa@test.com",
            phone="9840199999",
            password="Password123!"
        )
        self.client.login(username="admin_wa_branch", password="Password123!")

    def test_inbox_view_context_includes_active_branches(self):
        """Verify that the WhatsApp Inbox page loads active branches for the creation dropdown."""
        resp = self.client.get(reverse("inbox"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("branches", resp.context)
        branch_names = [b.name for b in resp.context["branches"]]
        self.assertIn("T. Nagar", branch_names)
        self.assertIn("Velachery", branch_names)

    def test_create_business_account_with_branch_foreign_key(self):
        """Verify POST /api/business-accounts/ with crm_branch persists the branch relation."""
        payload = {
            "name": "T. Nagar Admissions Line",
            "phone_number": "+91 98401 12345",
            "phone_number_id": "PNID_TEST_BRANCH_1",
            "business_account_id": "WABA_TEST_1",
            "crm_branch": self.branch_tn.id,
            "is_active": True,
        }
        resp = self.client.post(
            reverse("api-business-accounts"),
            data=payload,
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["crm_branch_id"], self.branch_tn.id)
        self.assertEqual(data["crm_branch_name"], "T. Nagar")

        ba = BusinessAccount.objects.get(phone_number_id="PNID_TEST_BRANCH_1")
        self.assertEqual(ba.crm_branch, self.branch_tn)

    def test_create_business_account_with_branch_id_alias(self):
        """Verify POST /api/business-accounts/ with crm_branch_id persists the branch relation."""
        payload = {
            "name": "Velachery Enquiries Line",
            "phone_number": "+91 98402 12345",
            "phone_number_id": "PNID_TEST_BRANCH_2",
            "crm_branch_id": self.branch_vel.id,
            "is_active": True,
        }
        resp = self.client.post(
            reverse("api-business-accounts"),
            data=payload,
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["crm_branch_id"], self.branch_vel.id)
        self.assertEqual(data["crm_branch_name"], "Velachery")

        ba = BusinessAccount.objects.get(phone_number_id="PNID_TEST_BRANCH_2")
        self.assertEqual(ba.crm_branch, self.branch_vel)
