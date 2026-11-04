from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from branches.models import Branch
from leads.models import Lead, PipelineStatus

User = get_user_model()


class PipelineStatusDeleteTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Pipeline Branch", status=Branch.Status.ACTIVE)
        self.admin = User.objects.create_superuser(
            username="admin_cr7_test",
            password="testpassword123",
            role="ADMIN",
        )
        self.client = Client()
        self.client.force_login(self.admin)

    def tearDown(self):
        Lead.objects.filter(status="Custom Test Stage").delete()
        PipelineStatus.objects.filter(name="Custom Test Stage").delete()
        self.admin.delete()
        self.branch.delete()

    def test_delete_blocked_when_leads_exist(self):
        """CR-7: Block delete if any lead has this status."""
        status_obj = PipelineStatus.objects.create(
            name="Custom Test Stage",
            stage_category="Custom",
            is_system_default=False,
            is_active=True,
        )

        Lead.objects.create(
            name="Test Lead CR7",
            phone="9988776655",
            email="test7@example.com",
            branch=self.branch,
            status="Custom Test Stage",
        )

        response = self.client.post(f'/admin/settings/pipeline-statuses/{status_obj.pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PipelineStatus.objects.filter(pk=status_obj.pk).exists())

    def test_delete_allowed_when_zero_leads(self):
        """CR-7: Allow delete if 0 leads use it."""
        status_obj = PipelineStatus.objects.create(
            name="Custom Test Stage",
            stage_category="Custom",
            is_system_default=False,
            is_active=True,
        )

        response = self.client.post(f'/admin/settings/pipeline-statuses/{status_obj.pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PipelineStatus.objects.filter(pk=status_obj.pk).exists())

    def test_cannot_delete_system_default_status(self):
        """CR-7: System default status cannot be deleted."""
        status_obj = PipelineStatus.objects.create(
            name="Custom Test Stage",
            stage_category="System",
            is_system_default=True,
            is_active=True,
        )

        response = self.client.post(f'/admin/settings/pipeline-statuses/{status_obj.pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PipelineStatus.objects.filter(pk=status_obj.pk).exists())
