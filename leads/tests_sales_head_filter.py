from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, UserRole
from branches.models import Branch
from leads.models import Lead, LeadStatus


class SalesHeadFilterOption3Tests(TestCase):
    def setUp(self):
        self.client = Client()

        self.branch1 = Branch.objects.create(name='Chennai Central', status='Active')
        self.branch2 = Branch.objects.create(name='Coimbatore Main', status='Active')

        self.sales_head = User.objects.create_user(
            username='test_sales_head',
            email='saleshead@example.com',
            password='password123',
            role=UserRole.SALES_HEAD,
            branch=self.branch1
        )

        self.telecaller = User.objects.create_user(
            username='test_tc1',
            email='tc1@example.com',
            password='password123',
            role=UserRole.TELECALLER,
            branch=self.branch1
        )

        # Create leads in branch1
        self.lead1 = Lead.objects.create(
            name='Kavitha R',
            phone='9840112233',
            email='kavitha@example.com',
            branch=self.branch1,
            assigned_telecaller=self.telecaller,
            status=LeadStatus.NEW,
            custom_fields={'degree': 'B.Tech', 'passed_out': '2024'}
        )
        self.lead2 = Lead.objects.create(
            name='Anand M',
            phone='9840223344',
            email='anand@example.com',
            branch=self.branch1,
            assigned_telecaller=self.telecaller,
            status=LeadStatus.CONTACTED,
            custom_fields={'degree': 'MCA', 'passed_out': '2023'}
        )

        # Lead in branch2 (not directly in sales_head branch unless centralized)
        self.lead3 = Lead.objects.create(
            name='Karthik S',
            phone='9840334455',
            email='karthik@example.com',
            branch=self.branch2,
            status=LeadStatus.NEW
        )

        self.client.login(username='test_sales_head', password='password123')

    def test_sales_head_leads_filter_panel_markup(self):
        response = self.client.get(reverse('manager_leads_list'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Views ribbon
        self.assertIn('All Views:', content)
        self.assertIn('All Leads', content)
        self.assertIn('All Active Leads', content)
        self.assertIn('+ Create View', content)

        # Option 3 Left Filter Panel
        self.assertIn('id="telecrmCreateViewPanel"', content)
        self.assertIn('class="telecrm-create-view-panel"', content)
        self.assertIn('Filter Builder', content)
        self.assertIn('id="cvActiveCountBadge"', content)

        # Categorized field catalog
        self.assertIn('Timestamps & Dates', content)
        self.assertIn('Lead Identity', content)
        self.assertIn('Allocation & Status', content)

        # Footer actions
        self.assertIn('resetAllConditions()', content)
        self.assertIn('id="cvBtnCount"', content)
        self.assertIn('Apply Filters', content)

    def test_sales_head_live_filter_count_api(self):
        # Live filter count for sales head should be scoped to their accessible leads
        response = self.client.get(reverse('api_filter_lead_count') + '?status=new')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        self.assertGreaterEqual(data.get('count'), 1)

    def test_sales_head_dynamic_filter_query_results(self):
        # Filter by status=contacted
        response = self.client.get(reverse('manager_leads_list') + '?status=contacted')
        self.assertEqual(response.status_code, 200)
        leads = list(response.context['page_obj'].object_list)
        lead_names = [l.name for l in leads]
        self.assertIn('Anand M', lead_names)
        self.assertNotIn('Kavitha R', lead_names)

    def test_sales_head_select_all_parity_with_superadmin(self):
        response = self.client.get(reverse('manager_leads_list'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Select all header checkbox and row checkboxes
        self.assertIn('id="select-all-leads"', content)
        self.assertIn('class="lead-row-select"', content)

        # Select all matching banner
        self.assertIn('id="select-all-matching-banner"', content)
        self.assertIn('id="btn-select-all-matching"', content)
        self.assertIn('toggleSelectAllMatching(true)', content)
        self.assertIn('id="all-matching-selected-indicator"', content)
        self.assertIn('toggleSelectAllMatching(false)', content)
        self.assertIn('Clear filter selection', content)

        # Bulk actions dock and deselect button
        self.assertIn('id="tp-bulk-actions-dock"', content)
        self.assertIn('id="selected-leads-count"', content)
        self.assertIn('id="btn-clear-selection"', content)

        # Global select-all matching script functions
        self.assertIn('window.selectAllMatchingFilters', content)
        self.assertIn('function toggleSelectAllMatching(enabled)', content)
        self.assertIn('function getSelectedLeadIds()', content)

