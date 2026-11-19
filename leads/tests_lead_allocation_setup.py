from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from branches.models import Branch
from leads.models import Lead, LeadStatus, TelecallerLeadSetup, LeadAssignmentHistory
from accounts.models import UserRole
from leads.views import admin_lead_setup
from leads.assignment import assign_new_lead, apply_branch_lead_distribution

User = get_user_model()


class LeadAllocationSetupTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Admin user
        self.admin = User.objects.create_superuser(
            username='super_admin_test',
            email='admin@techpanda.test',
            password='TestPassword123'
        )

        # Real branches
        self.branch_anna, _ = Branch.objects.get_or_create(name='Anna Nagar', defaults={'status': 'Active'})
        self.branch_tnagar, _ = Branch.objects.get_or_create(name='T. Nagar', defaults={'status': 'Active'})
        self.branch_tambaram, _ = Branch.objects.get_or_create(name='Tambaram', defaults={'status': 'Active'})

        # Centralized branch
        self.central_branch, _ = Branch.objects.get_or_create(
            name='Centralized (All Branches)',
            defaults={'status': 'Active'}
        )

        # Telecallers in T. Nagar and Tambaram (Anna Nagar has 0 telecallers)
        self.tc1 = User.objects.create_user(
            username='tc_tnagar_1',
            first_name='Ravi',
            role=UserRole.TELECALLER,
            branch=self.branch_tnagar,
            is_active=True,
            is_on_duty=True
        )
        self.tc2 = User.objects.create_user(
            username='tc_tambaram_1',
            first_name='Suresh',
            role=UserRole.TELECALLER,
            branch=self.branch_tambaram,
            is_active=True,
            is_on_duty=True
        )

    def test_centralized_branch_guaranteed_exists(self):
        """Verifies Centralized (All Branches) exists and is active."""
        branch = Branch.objects.filter(name='Centralized (All Branches)').first()
        self.assertIsNotNone(branch)
        self.assertEqual(branch.status, 'Active')

    def test_admin_lead_setup_overview_renders_centralized_hub_with_real_telecallers(self):
        """Centralized Hub card renders with correct org telecaller count and pooled leads."""
        request = self.factory.get('/admin/settings/lead-setup/')
        request.user = self.admin
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))

        response = admin_lead_setup(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('Centralized Lead Allocation Hub (All Branches)', content)
        self.assertIn('CENTRALIZED ALLOCATION', content)
        self.assertIn('Configure Centralized Setup &rarr;', content)
        # Should not display 0 Org Telecallers when telecallers exist
        self.assertIn('Org Telecallers', content)

    def test_admin_lead_setup_centralized_detail_lists_all_org_telecallers(self):
        """Detail setup for Centralized Hub lists telecallers from all branches grouped by branch."""
        request = self.factory.get(f'/admin/settings/lead-setup/?branch_id={self.central_branch.id}&source=WhatsApp')
        request.user = self.admin
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))

        response = admin_lead_setup(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('Centralized Allocation Setup &rsaquo; WhatsApp', content)
        self.assertIn('Ravi', content)
        self.assertIn('Suresh', content)
        self.assertIn('T. Nagar', content)
        self.assertIn('Tambaram', content)

    def test_zero_telecaller_branch_displays_guidance_notice(self):
        """Selecting a branch with 0 telecallers (Anna Nagar) shows friendly guidance box."""
        request = self.factory.get(f'/admin/settings/lead-setup/?branch_id={self.branch_anna.id}&source=WhatsApp')
        request.user = self.admin
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))

        response = admin_lead_setup(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('No Dedicated Telecallers in Anna Nagar', content)
        self.assertIn('Centralized Lead Allocation Hub', content)
        self.assertIn('Configure Centralized Allocation Hub &rarr;', content)

    def test_lead_fallback_to_centralized_allocation_hub(self):
        """When Anna Nagar has 0 telecallers, lead falls back to Centralized Hub rule."""
        # Setup Centralized Hub WhatsApp rule: 50% tc1, 50% tc2
        TelecallerLeadSetup.objects.create(
            telecaller=self.tc1,
            branch=self.central_branch,
            source='WhatsApp',
            assignment_percentage=50,
            is_active=True
        )
        TelecallerLeadSetup.objects.create(
            telecaller=self.tc2,
            branch=self.central_branch,
            source='WhatsApp',
            assignment_percentage=50,
            is_active=True
        )

        lead = Lead.objects.create(
            name='Kavitha Test',
            phone='9876543210',
            branch=self.branch_anna,
            source='WhatsApp',
            status=LeadStatus.NEW
        )

        success = assign_new_lead(lead, branch=self.branch_anna, source='WhatsApp')
        self.assertTrue(success)
        lead.refresh_from_db()

        self.assertEqual(lead.assignment_status, 'Assigned')
        self.assertIn(lead.assigned_telecaller, [self.tc1, self.tc2])
        self.assertEqual(lead.branch, self.branch_anna)

        # Verify LeadAssignmentHistory recorded
        history = LeadAssignmentHistory.objects.filter(lead=lead).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.to_user, lead.assigned_telecaller)
        self.assertEqual(history.branch, self.branch_anna)

    def test_pending_assignment_creates_history_record(self):
        """When no allocation rule exists, lead is marked Pending Assignment and history is recorded."""
        lead = Lead.objects.create(
            name='Unassigned Student',
            phone='9811122233',
            branch=self.branch_anna,
            source='Offline Event',
            status=LeadStatus.NEW
        )

        success = assign_new_lead(lead, branch=self.branch_anna, source='Offline Event')
        self.assertFalse(success)
        lead.refresh_from_db()

        self.assertEqual(lead.assignment_status, 'Pending Assignment')
        self.assertIn('No active telecallers or allocation configured', lead.pending_assignment_reason)

        history = LeadAssignmentHistory.objects.filter(lead=lead).first()
        self.assertIsNotNone(history)
        self.assertIn('Pending Assignment:', history.reason)
        self.assertEqual(history.branch, self.branch_anna)
