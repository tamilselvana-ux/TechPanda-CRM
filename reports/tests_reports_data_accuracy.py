from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, UserRole
from branches.models import Branch
from leads.models import Lead, LeadStatus
from calls.models import CallHistory
from reports.services import get_dashboard_report_data, CANONICAL_CHANNELS, resolve_canonical_channel_q


class ReportsDataAccuracyTests(TestCase):
    def setUp(self):
        self.branch_anna, _ = Branch.objects.get_or_create(name='Anna Nagar', defaults={'status': 'Active'})
        self.branch_porur, _ = Branch.objects.get_or_create(name='Porur', defaults={'status': 'Active'})

        self.admin = User.objects.create_superuser(
            username='admin_accuracy_tester',
            password='password123',
            email='admin_acc@test.com',
            role=UserRole.ADMIN
        )

        self.manager = User.objects.create_user(
            username='manager_accuracy_tester',
            password='password123',
            email='manager_acc@test.com',
            role=UserRole.SALES_HEAD,
            branch=self.branch_anna
        )

        self.telecaller = User.objects.create_user(
            username='tc_accuracy_tester',
            password='password123',
            email='tc_acc@test.com',
            role=UserRole.TELECALLER,
            branch=self.branch_anna
        )

        # Create distinct test leads covering canonical channels and statuses
        self.lead_meta_form = Lead.objects.create(
            name='Meta Form Lead',
            phone='9000000001',
            status=LeadStatus.NEW,
            source='Meta Ads',
            branch=self.branch_anna
        )

        self.lead_meta_wa = Lead.objects.create(
            name='WhatsApp Lead',
            phone='9000000002',
            status=LeadStatus.CONTACTED,
            source='WhatsApp',
            branch=self.branch_anna
        )

        self.lead_google_ad = Lead.objects.create(
            name='Google Ad Lead',
            phone='9000000003',
            status=LeadStatus.INTERESTED,
            source='Google Ad',
            branch=self.branch_porur
        )

        self.lead_google_seo = Lead.objects.create(
            name='SEO Lead',
            phone='9000000004',
            status=LeadStatus.NEW,
            source='Google SEO',
            branch=self.branch_porur
        )

        self.lead_instagram = Lead.objects.create(
            name='Instagram Lead',
            phone='9000000005',
            status=LeadStatus.NO_ANSWER,
            source='Instagram',
            branch=self.branch_anna
        )

        self.lead_google_call = Lead.objects.create(
            name='Google Call Lead',
            phone='9000000006',
            status=LeadStatus.CONVERTED,
            source='Google Call',
            branch=self.branch_anna
        )

        self.lead_influencer = Lead.objects.create(
            name='Influencer Lead',
            phone='9000000007',
            status=LeadStatus.LOST,
            source='Influencer',
            branch=self.branch_porur
        )

        self.lead_other_direct = Lead.objects.create(
            name='TeleCRM Direct Lead',
            phone='9000000008',
            status=LeadStatus.ENROLLED,
            source='TeleCRM',
            branch=self.branch_anna
        )

        self.lead_unassigned = Lead.objects.create(
            name='Manual Walkin Lead',
            phone='9000000009',
            status=LeadStatus.JOINED,
            source='Manual',
            branch=None
        )

        # Add a call history record
        self.call1 = CallHistory.objects.create(
            lead=self.lead_meta_form,
            caller=self.telecaller,
            call_status='Completed',
            call_outcome='Interested',
            duration=60
        )

    def test_01_canonical_channels_sum_equals_total_leads(self):
        data = get_dashboard_report_data(self.admin, {'date_filter': 'all'})
        total_leads = data['kpi_total_leads']
        self.assertEqual(total_leads, 9)

        channel_sum = sum(card['count'] for card in data['channels'])
        self.assertEqual(channel_sum, total_leads)

        donut_sum = sum(data['donut_chart']['values'])
        self.assertEqual(donut_sum, total_leads)

    def test_02_channel_drilldown_finds_leads_in_admin_and_manager_views(self):
        client = Client()
        client.force_login(self.admin)

        # Test Meta Lead Form
        res_meta_form = client.get(reverse('admin_leads_list') + '?view=all&channel=Meta+Lead+Form')
        self.assertEqual(res_meta_form.status_code, 200)
        self.assertContains(res_meta_form, 'Meta Form Lead')

        # Test Meta WhatsApp
        res_meta_wa = client.get(reverse('admin_leads_list') + '?view=all&channel=Meta+WhatsApp')
        self.assertEqual(res_meta_wa.status_code, 200)
        self.assertContains(res_meta_wa, 'WhatsApp Lead')

        # Test Other / Direct
        res_other = client.get(reverse('admin_leads_list') + '?view=all&channel=Other+/+Direct')
        self.assertEqual(res_other.status_code, 200)
        self.assertContains(res_other, 'TeleCRM Direct Lead')
        self.assertContains(res_other, 'Manual Walkin Lead')

    def test_03_default_date_fallback_this_month(self):
        # Empty parameters: when today has no leads created today, fallback activates
        data = get_dashboard_report_data(self.admin, {})
        # Leads created in setUp are created with timezone.now(), so they match this_month
        self.assertIn(data['date_filter'], ['today', 'this_month'])
        self.assertGreater(data['kpi_total_leads'], 0)

    def test_04_reports_api_data_payload_structure(self):
        client = Client()
        client.force_login(self.admin)

        res = client.get(reverse('reports_api_data') + '?date_filter=all')
        self.assertEqual(res.status_code, 200)
        json_data = res.json()

        self.assertIn('channels', json_data)
        self.assertEqual(len(json_data['channels']), 8)
        self.assertIn('donut_chart', json_data)
        self.assertIn('stacked_chart', json_data)
        self.assertIn('outcomes_chart', json_data)
        self.assertIn('branch_rows', json_data)
        self.assertIn('branch_totals', json_data)
        self.assertIn('leads_url', json_data)
        self.assertEqual(json_data['kpi_total_leads'], 9)

    def test_05_enrolled_leads_in_conversion_metrics(self):
        data = get_dashboard_report_data(self.admin, {'date_filter': 'all'})
        # Converted leads should include: lead_google_call (CONVERTED), lead_other_direct (ENROLLED), lead_unassigned (JOINED) = 3
        self.assertEqual(data['converted_leads_count'], 3)

        client = Client()
        client.force_login(self.admin)

        res_prospected = client.get(reverse('admin_leads_list') + '?view=all&status_group=prospected')
        self.assertEqual(res_prospected.status_code, 200)
        self.assertContains(res_prospected, 'TeleCRM Direct Lead')
        self.assertContains(res_prospected, 'Manual Walkin Lead')
        self.assertContains(res_prospected, 'Google Call Lead')

    def test_06_branch_wise_summary_math_integrity(self):
        data = get_dashboard_report_data(self.admin, {'date_filter': 'all'})
        branch_rows = data['branch_rows']
        branch_totals = data['branch_totals']

        # Each branch row's channel breakdown must equal the row's total_leads
        total_from_rows = 0
        for row in branch_rows:
            self.assertEqual(sum(row['channels']), row['total_leads'])
            total_from_rows += row['total_leads']

        self.assertEqual(total_from_rows, data['kpi_total_leads'])
        self.assertEqual(branch_totals['total_leads'], data['kpi_total_leads'])
        self.assertEqual(sum(branch_totals['channels']), data['kpi_total_leads'])
