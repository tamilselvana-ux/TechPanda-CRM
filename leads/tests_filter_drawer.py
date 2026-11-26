from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, UserRole
from branches.models import Branch
from leads.models import Lead, LeadStatus


class LeftFilterPanelOption3Tests(TestCase):
    def setUp(self):
        self.client = Client()

        self.branch, _ = Branch.objects.get_or_create(
            name='Chennai Main',
            defaults={'status': 'Active'}
        )

        self.superadmin = User.objects.create_superuser(
            username='admin_filter_test',
            email='admin_filter_test@example.com',
            password='password123',
            role=UserRole.SUPERADMIN
        )

        # Create test leads
        self.lead1 = Lead.objects.create(
            name='Ramesh Kumar',
            phone='9876543210',
            email='ramesh@example.com',
            branch=self.branch,
            status=LeadStatus.NEW,
            custom_fields={'degree': 'B.E', 'passed_out': '2024'}
        )
        self.lead2 = Lead.objects.create(
            name='Priya Sharma',
            phone='9876543211',
            email='priya@example.com',
            branch=self.branch,
            status=LeadStatus.CONTACTED,
            custom_fields={'degree': 'MCA', 'passed_out': '2023'}
        )

        self.client.login(username='admin_filter_test', password='password123')

    def test_filter_panel_markup_and_header(self):
        response = self.client.get(reverse('admin_leads_list'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Left split-panel filter builder
        self.assertIn('id="telecrmCreateViewPanel"', content)
        self.assertIn('class="telecrm-create-view-panel"', content)
        self.assertIn('.telecrm-layout-wrapper', content)
        self.assertIn('.telecrm-main-workspace', content)

        # Panel header elements
        self.assertIn('Filter Builder', content)
        self.assertIn('id="cvActiveCountBadge"', content)
        self.assertIn('toggleCreateViewPanel(false)', content)

    def test_categorized_field_catalog_groups(self):
        response = self.client.get(reverse('admin_leads_list'))
        content = response.content.decode('utf-8')

        # Check the 3 categorized groups
        self.assertIn('Timestamps & Dates', content)
        self.assertIn('Lead Identity', content)
        self.assertIn('Allocation & Status', content)

        # Check field catalog items
        required_fields = [
            'status_updated_on', 'created_on', 'name', 'phone',
            'degree', 'passed_out', 'working_status', 'purpose',
            'status', 'branch', 'preferred_branch', 'telecaller',
            'created_by', 'source'
        ]
        for field in required_fields:
            self.assertIn(f'data-field="{field}"', content, f'Missing catalog item for {field}')

        # Check that SVG icons exist in catalog
        self.assertIn('cv-field-icon', content)
        self.assertIn('<svg', content)

    def test_panel_footer_actions(self):
        response = self.client.get(reverse('admin_leads_list'))
        content = response.content.decode('utf-8')

        # Reset All, Apply buttons with live count badge
        self.assertIn('resetAllConditions()', content)
        self.assertIn('id="cvBtnCount"', content)
        self.assertIn('Apply Filters (', content)

    def test_live_filter_count_api(self):
        response = self.client.get(reverse('api_filter_lead_count') + '?status=new')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        self.assertEqual(data.get('count'), 1)
