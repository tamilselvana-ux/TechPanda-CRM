from datetime import datetime, time, timedelta
import csv
import io

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import User, UserRole
from branches.models import Branch
from lead_channels.models import Channel
from products.models import Product
from leads.models import Lead, LeadStatus


class MarketingTeamPortalTests(TestCase):
    """
    Comprehensive verification test suite for Marketing Team role,
    read-only lead access, dynamic filtering, dashboard metrics,
    and security enforcement.
    """

    def setUp(self):
        self.client = Client()

        # Create branches
        self.branch_a = Branch.objects.create(name="Anna Nagar Center", status="Active")
        self.branch_b = Branch.objects.create(name="Porur Center", status="Active")

        # Create Superadmin
        self.admin_user = User.objects.create_user(
            username="admin_test",
            email="admin@techpanda.test",
            password="Password123!",
            role=UserRole.ADMIN,
            is_active=True
        )

        # Create Marketing User
        self.marketing_user = User.objects.create_user(
            username="marketing_analyst",
            first_name="Priya",
            last_name="Rajan",
            email="priya.marketing@techpanda.test",
            phone="9876543210",
            password="Password123!",
            role=UserRole.MARKETING,
            is_active=True
        )

        # Create Channels and Products
        self.channel_meta = Channel.objects.create(name="Meta Ads", status="Active")
        self.channel_google = Channel.objects.create(name="Google Search", status="Active")
        self.product_python = Product.objects.create(name="Full Stack Python", status="Active")

        # Create sample leads across branches and sources
        self.lead_1 = Lead.objects.create(
            name="Aravind Kumar",
            phone="9840111222",
            email="aravind@example.com",
            branch=self.branch_a,
            channel=self.channel_meta,
            source="Meta Ads",
            product=self.product_python,
            status=LeadStatus.NEW,
            rating=4
        )
        self.lead_2 = Lead.objects.create(
            name="Bhavani Shankar",
            phone="9840222333",
            email="bhavani@example.com",
            branch=self.branch_b,
            channel=self.channel_google,
            source="Google Search",
            product=self.product_python,
            status=LeadStatus.CONVERTED,
            rating=5
        )
        self.lead_3 = Lead.objects.create(
            name="Chandran Selvam",
            phone="9840333444",
            email="chandran@example.com",
            branch=None,
            channel=self.channel_meta,
            source="WhatsApp Bot",
            product=self.product_python,
            status=LeadStatus.CONTACTED,
            rating=3
        )

    def test_01_user_role_definition_and_properties(self):
        """Verify UserRole.MARKETING, is_marketing_user, and display_role."""
        self.assertEqual(self.marketing_user.role, UserRole.MARKETING)
        self.assertTrue(self.marketing_user.is_marketing_user)
        self.assertFalse(self.marketing_user.is_admin_user)
        self.assertFalse(self.marketing_user.is_telecaller_user)
        self.assertEqual(self.marketing_user.display_role, "Marketing Team")

    def test_02_login_redirect_routes_marketing_to_dashboard(self):
        """Verify login_redirect resolves to marketing_dashboard for Marketing role."""
        self.client.login(username="marketing_analyst", password="Password123!")
        response = self.client.get(reverse('login_redirect'))
        self.assertRedirects(response, reverse('marketing_dashboard'))

    def test_03_marketing_dashboard_metrics(self):
        """Verify marketing_dashboard computes accurate KPIs, sources, and branches."""
        self.client.login(username="marketing_analyst", password="Password123!")
        response = self.client.get(reverse('marketing_dashboard'))
        self.assertEqual(response.status_code, 200)

        ctx = response.context
        self.assertEqual(ctx['total_leads'], 3)
        self.assertEqual(ctx['converted_leads'], 1)
        self.assertEqual(ctx['new_leads_count'], 1)
        self.assertAlmostEqual(ctx['conversion_rate'], 33.3, places=1)
        self.assertTrue(ctx['is_marketing_user'])

        # Verify source breakdown
        sources = {item['source']: item['total'] for item in ctx['source_stats']}
        self.assertIn("Meta Ads", sources)
        self.assertIn("Google Search", sources)

    def test_04_universal_lead_visibility_across_all_branches(self):
        """Verify marketing_leads_list shows leads from Branch A, Branch B, and unassigned."""
        self.client.login(username="marketing_analyst", password="Password123!")
        response = self.client.get(reverse('marketing_leads_list'))
        self.assertEqual(response.status_code, 200)

        leads = list(response.context['leads'])
        lead_ids = [l.pk for l in leads]
        self.assertIn(self.lead_1.pk, lead_ids)
        self.assertIn(self.lead_2.pk, lead_ids)
        self.assertIn(self.lead_3.pk, lead_ids)
        self.assertTrue(response.context['is_marketing_readonly'])

    def test_05_dynamic_filters_on_marketing_leads_list(self):
        """Verify dynamic filters: search, branch, and status filtering."""
        self.client.login(username="marketing_analyst", password="Password123!")

        # Filter by branch
        resp_branch = self.client.get(reverse('marketing_leads_list') + f'?branch={self.branch_a.id}')
        self.assertEqual(resp_branch.status_code, 200)
        leads_branch = list(resp_branch.context['leads'])
        self.assertEqual(len(leads_branch), 1)
        self.assertEqual(leads_branch[0].name, "Aravind Kumar")

        # Filter by status
        resp_status = self.client.get(reverse('marketing_leads_list') + '?status=Converted')
        self.assertEqual(resp_status.status_code, 200)
        leads_status = list(resp_status.context['leads'])
        self.assertEqual(len(leads_status), 1)
        self.assertEqual(leads_status[0].name, "Bhavani Shankar")

        # Search by name condition
        resp_search = self.client.get(reverse('marketing_leads_list') + '?search=Chandran')
        self.assertEqual(resp_search.status_code, 200)
        leads_search = list(resp_search.context['leads'])
        self.assertEqual(len(leads_search), 1)
        self.assertEqual(leads_search[0].name, "Chandran Selvam")

        # Dynamic condition: filter by phone
        resp_phone = self.client.get(reverse('marketing_leads_list') + '?phone=9840333')
        self.assertEqual(resp_phone.status_code, 200)
        leads_phone = list(resp_phone.context['leads'])
        self.assertEqual(len(leads_phone), 1)
        self.assertEqual(leads_phone[0].name, "Chandran Selvam")

    def test_06_read_only_protection_blocks_mutations(self):
        """Verify Marketing user cannot execute lead modifications or deletions."""
        self.client.login(username="marketing_analyst", password="Password123!")

        # 1. api_update_lead_status -> 403 Forbidden
        resp_status_update = self.client.post(
            reverse('api_update_lead_status'),
            data={'lead_id': self.lead_1.pk, 'new_status': LeadStatus.INTERESTED},
            content_type='application/json'
        )
        self.assertEqual(resp_status_update.status_code, 403)

        # 2. api_bulk_action -> 403 Forbidden
        resp_bulk = self.client.post(
            reverse('api_bulk_action'),
            data={'action': 'update_status', 'lead_ids': [self.lead_1.pk], 'new_status': 'Lost'},
            content_type='application/json'
        )
        self.assertEqual(resp_bulk.status_code, 403)

        # 3. admin_lead_delete -> 302 Redirect (permission denied by admin_required)
        resp_delete = self.client.post(reverse('admin_lead_delete', args=[self.lead_1.pk]))
        self.assertEqual(resp_delete.status_code, 302)
        # Confirm lead is not deleted
        self.assertTrue(Lead.objects.filter(pk=self.lead_1.pk).exists())

        # 4. admin_lead_edit -> 302 Redirect (permission denied by admin_required)
        resp_edit = self.client.get(reverse('admin_lead_edit', args=[self.lead_1.pk]))
        self.assertEqual(resp_edit.status_code, 302)

    def test_07_marketing_lead_detail_read_only(self):
        """Verify marketing_lead_detail renders read-only profile."""
        self.client.login(username="marketing_analyst", password="Password123!")
        response = self.client.get(reverse('marketing_lead_detail', args=[self.lead_1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_marketing_readonly'])
        self.assertIsNone(response.context['edit_url_name'])
        self.assertEqual(response.context['list_url_name'], 'marketing_leads_list')

    def test_08_marketing_export_csv(self):
        """Verify marketing_export_leads generates CSV output."""
        self.client.login(username="marketing_analyst", password="Password123!")
        response = self.client.get(reverse('marketing_export_leads'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="marketing_leads_export.csv"', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        self.assertGreaterEqual(len(rows), 4)  # 1 header + 3 leads
        self.assertEqual(rows[0][0], 'Lead ID')
        self.assertEqual(rows[0][1], 'Name')

    def test_09_staff_management_integration(self):
        """Verify admin can view and toggle marketing staff."""
        self.client.login(username="admin_test", password="Password123!")

        # Staff counts in context processor
        resp_admin = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp_admin.status_code, 200)
        staff_counts = resp_admin.context['staff_counts']
        self.assertIn('marketing', staff_counts)
        self.assertEqual(staff_counts['marketing'], 1)

        # Marketing staff list view
        resp_list = self.client.get(reverse('admin_marketing_users_list'))
        self.assertEqual(resp_list.status_code, 200)
        self.assertContains(resp_list, "Priya Rajan")

        # Toggle status
        resp_toggle = self.client.post(reverse('admin_marketing_user_toggle_status', args=[self.marketing_user.pk]))
        self.assertEqual(resp_toggle.status_code, 302)
        self.marketing_user.refresh_from_db()
        self.assertFalse(self.marketing_user.is_active)

    def test_10_marketing_dashboard_renders_with_null_channel_and_source(self):
        """Verify marketing dashboard renders cleanly without template errors when leads have null channels or sources."""
        self.client.login(username="marketing_analyst", password="Password123!")

        # Create a lead with null channel, null source, null branch
        Lead.objects.create(
            name="Null Channel Lead",
            phone="9000099999",
            email="null@test.com",
            channel=None,
            source="",
            branch=None,
            status=LeadStatus.NEW
        )

        response = self.client.get(reverse('marketing_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Null Channel Lead")
        self.assertContains(response, "Direct")
