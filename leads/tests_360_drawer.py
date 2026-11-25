from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, UserRole
from branches.models import Branch
from leads.models import Lead, LeadStatus
from accounts.permissions import get_accessible_branch_ids, can_access_lead


class Student360DrawerAndCentralizedSalesHeadTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Setup branches
        self.central_branch, _ = Branch.objects.get_or_create(
            name='Centralized (All Branches)',
            defaults={'status': 'Active'}
        )
        self.branch_anna, _ = Branch.objects.get_or_create(
            name='Anna Nagar Test',
            defaults={'status': 'Active'}
        )
        self.branch_coimbatore, _ = Branch.objects.get_or_create(
            name='Coimbatore Test',
            defaults={'status': 'Active'}
        )

        # Centralized Sales Head
        self.central_sales_head = User.objects.create_user(
            username='central_sh',
            email='central_sh@example.com',
            password='password123',
            role=UserRole.SALES_HEAD,
            branch=self.central_branch
        )

        # Local Branch Sales Head
        self.local_sales_head = User.objects.create_user(
            username='local_sh',
            email='local_sh@example.com',
            password='password123',
            role=UserRole.SALES_HEAD,
            branch=self.branch_anna
        )

        # Superadmin
        self.superadmin = User.objects.create_superuser(
            username='admin_user',
            email='admin@example.com',
            password='password123',
            role=UserRole.SUPERADMIN
        )

        # Create leads in different branches
        self.lead_anna = Lead.objects.create(
            name='Student Anna',
            phone='9876543210',
            email='anna@student.com',
            branch=self.branch_anna,
            status=LeadStatus.NEW
        )
        self.lead_coimbatore = Lead.objects.create(
            name='Student Coimbatore',
            phone='9876543211',
            email='cbe@student.com',
            branch=self.branch_coimbatore,
            status=LeadStatus.CONTACTED
        )
        self.lead_unassigned = Lead.objects.create(
            name='Student Unassigned Pool',
            phone='9876543212',
            email='pool@student.com',
            branch=None,
            status=LeadStatus.NEW
        )

    def test_360_drawer_endpoint_resolves_and_returns_200(self):
        """Verify /leads/<id>/360-data/ returns HTTP 200 with complete timeline and student payload."""
        self.client.force_login(self.central_sales_head)
        url = f"/leads/{self.lead_anna.pk}/360-data/"
        res = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertTrue(data.get('success'))
        self.assertIn('student', data)
        self.assertIn('summary', data)
        self.assertIn('timeline', data)
        self.assertEqual(data['student']['name'], 'Student Anna')
        self.assertEqual(data['student']['phone'], '9876543210')

    def test_360_legacy_endpoint_resolves_and_returns_200(self):
        """Verify /leads/<id>/360/ also resolves and returns HTTP 200 for backward compatibility."""
        self.client.force_login(self.central_sales_head)
        url = f"/leads/{self.lead_anna.pk}/360/"
        res = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get('success'))

    def test_centralized_sales_head_gets_all_branch_ids(self):
        """Verify Centralized Sales Head receives all branch IDs across the organization."""
        accessible_ids = get_accessible_branch_ids(self.central_sales_head)
        all_branch_ids = list(Branch.objects.values_list('id', flat=True))
        self.assertEqual(set(accessible_ids), set(all_branch_ids))

    def test_local_sales_head_gets_only_assigned_branch_id(self):
        """Verify Local Sales Head is restricted to their assigned branch ID."""
        accessible_ids = get_accessible_branch_ids(self.local_sales_head)
        self.assertEqual(accessible_ids, [self.branch_anna.id])

    def test_centralized_sales_head_can_access_leads_in_all_branches(self):
        """Verify can_access_lead returns True for Centralized Sales Head across all branches and unassigned leads."""
        self.assertTrue(can_access_lead(self.central_sales_head, self.lead_anna))
        self.assertTrue(can_access_lead(self.central_sales_head, self.lead_coimbatore))
        self.assertTrue(can_access_lead(self.central_sales_head, self.lead_unassigned))

    def test_local_sales_head_restricted_to_assigned_branch(self):
        """Verify can_access_lead restricts Local Sales Head to their branch leads."""
        self.assertTrue(can_access_lead(self.local_sales_head, self.lead_anna))
        self.assertFalse(can_access_lead(self.local_sales_head, self.lead_coimbatore))

    def test_centralized_sales_head_sees_all_leads_on_manager_leads_list(self):
        """Verify /manager/leads/ displays all organization leads and unassigned pool for Centralized Sales Head."""
        self.client.force_login(self.central_sales_head)
        res = self.client.get('/manager/leads/')
        self.assertEqual(res.status_code, 200)

        leads_in_context = list(res.context['page_obj'])
        lead_ids_in_context = [ld.id for ld in leads_in_context]

        self.assertIn(self.lead_anna.id, lead_ids_in_context)
        self.assertIn(self.lead_coimbatore.id, lead_ids_in_context)
        self.assertIn(self.lead_unassigned.id, lead_ids_in_context)

    def test_local_sales_head_sees_only_local_leads_on_manager_leads_list(self):
        """Verify /manager/leads/ displays only local branch leads for Local Sales Head."""
        self.client.force_login(self.local_sales_head)
        res = self.client.get('/manager/leads/')
        self.assertEqual(res.status_code, 200)

        leads_in_context = list(res.context['page_obj'])
        lead_ids_in_context = [ld.id for ld in leads_in_context]

        self.assertIn(self.lead_anna.id, lead_ids_in_context)
        self.assertNotIn(self.lead_coimbatore.id, lead_ids_in_context)
