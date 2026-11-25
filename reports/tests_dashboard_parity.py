from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, UserRole
from branches.models import Branch
from leads.models import Lead, LeadStatus
from reports.services import get_management_chart_data


class DashboardParityTests(TestCase):
    def setUp(self):
        self.branch1, _ = Branch.objects.get_or_create(name='Anna Nagar', defaults={'status': 'Active'})
        self.branch2, _ = Branch.objects.get_or_create(name='Velachery', defaults={'status': 'Active'})
        self.central_branch, _ = Branch.objects.get_or_create(name='Centralized (All Branches)', defaults={'status': 'Active'})

        self.admin = User.objects.create_superuser(
            username='superadmin_parity',
            email='admin@techpanda.test',
            password='Password123!',
            role=UserRole.SUPERADMIN
        )

        self.tc1 = User.objects.create_user(
            username='tc_pool',
            email='tc_pool@techpanda.test',
            password='Password123!',
            role=UserRole.TELECALLER,
            branch=None,
            is_active=True
        )

        # 3 leads in branch 1
        for i in range(3):
            Lead.objects.create(
                name=f'Branch1 Lead {i}',
                phone=f'984000100{i}',
                branch=self.branch1,
                status=LeadStatus.NEW
            )

        # 2 leads in branch 2
        for i in range(2):
            Lead.objects.create(
                name=f'Branch2 Lead {i}',
                phone=f'984000200{i}',
                branch=self.branch2,
                status=LeadStatus.NEW
            )

        # 4 leads with NO branch (central pool)
        for i in range(4):
            Lead.objects.create(
                name=f'Unassigned Lead {i}',
                phone=f'984000300{i}',
                branch=None,
                status=LeadStatus.NEW
            )

        self.client = Client()
        self.client.force_login(self.admin)

    def test_management_chart_data_parity_with_total_leads(self):
        """Verify that organization-wide status chart data total exactly equals Lead.objects.count()."""
        total_leads_count = Lead.objects.count()
        self.assertEqual(total_leads_count, 9)

        all_branch_ids = list(Branch.objects.values_list('id', flat=True))
        chart_data = get_management_chart_data(branch_ids=all_branch_ids, include_unassigned=True)

        chart_sum = sum(chart_data['status_chart']['data'])
        self.assertEqual(chart_sum, total_leads_count, "Donut chart total must match total leads in DB")

    def test_management_charts_api_endpoint_parity_for_admin(self):
        """API endpoint /api/management-charts/ returns status data summing to total leads when no branch filter."""
        res = self.client.get(reverse('management_charts_api'))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('status_chart', data)
        chart_sum = sum(data['status_chart']['data'])
        self.assertEqual(chart_sum, Lead.objects.count())

    def test_lead_setup_branch_available_leads_no_unassigned_duplication(self):
        """Individual branch cards must only count leads assigned to that branch, not unassigned pool."""
        res = self.client.get(reverse('admin_lead_setup'))
        self.assertEqual(res.status_code, 200)
        branch_data = res.context['branch_data']

        b1_data = next((b for b in branch_data if b['branch'].id == self.branch1.id), None)
        self.assertIsNotNone(b1_data)
        # Branch 1 has 3 leads. Before fix it was 3 + 4 = 7. Now it must be exactly 3.
        self.assertEqual(b1_data['available_leads_count'], 3)

        b2_data = next((b for b in branch_data if b['branch'].id == self.branch2.id), None)
        self.assertIsNotNone(b2_data)
        self.assertEqual(b2_data['available_leads_count'], 2)

        # Centralized Hub card counts pooled leads (4 unassigned)
        central_data = next((b for b in branch_data if b['is_centralized']), None)
        self.assertIsNotNone(central_data)
        self.assertEqual(central_data['available_leads_count'], 9)
