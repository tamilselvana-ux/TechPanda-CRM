import os
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import UserRole
from branches.models import Branch
from leads.models import Lead
from followups.models import FollowUp
from calls.models import CallHistory

User = get_user_model()


class UniversalUserActionsTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Admin user
        self.admin_user = User.objects.create_user(
            username='admin_boss',
            email='admin_boss@techpanda.test',
            password='Password123!',
            role=UserRole.ADMIN,
            is_staff=True,
            is_superuser=True
        )

        # Branch
        self.branch = Branch.objects.create(name='Chennai Central')

        # Telecaller
        self.telecaller = User.objects.create_user(
            username='tc_arun',
            first_name='Arun',
            last_name='Kumar',
            email='arun@techpanda.test',
            password='Password123!',
            role=UserRole.TELECALLER,
            branch=self.branch
        )

        # Counselor
        self.counselor = User.objects.create_user(
            username='coun_priya',
            first_name='Priya',
            last_name='Dharshini',
            email='priya@techpanda.test',
            password='Password123!',
            role=UserRole.COUNSELOR,
            branch=self.branch
        )

        # Sales Head / Manager
        self.sales_head = User.objects.create_user(
            username='sh_karthik',
            first_name='Karthik',
            last_name='Raja',
            email='karthik@techpanda.test',
            password='Password123!',
            role=UserRole.SALES_HEAD
        )

        # Branch Head
        self.branch_head = User.objects.create_user(
            username='bh_suresh',
            first_name='Suresh',
            last_name='Raina',
            email='suresh@techpanda.test',
            password='Password123!',
            role=UserRole.BRANCH_HEAD,
            branch=self.branch
        )

        # Branch Admin
        self.branch_admin = User.objects.create_user(
            username='ba_divya',
            first_name='Divya',
            last_name='Nair',
            email='divya@techpanda.test',
            password='Password123!',
            role=UserRole.BRANCH_ADMIN,
            branch=self.branch
        )

        # Receptionist
        self.receptionist = User.objects.create_user(
            username='rec_anita',
            first_name='Anita',
            last_name='Sharma',
            email='anita@techpanda.test',
            password='Password123!',
            role=UserRole.RECEPTIONIST,
            branch=self.branch
        )

        # Accountant
        self.accountant = User.objects.create_user(
            username='acc_ramesh',
            first_name='Ramesh',
            last_name='Babu',
            email='ramesh@techpanda.test',
            password='Password123!',
            role=UserRole.ACCOUNTANT,
            branch=self.branch
        )

        # Marketing Member
        self.marketing_user = User.objects.create_user(
            username='mkt_deepa',
            first_name='Deepa',
            last_name='Lakshmi',
            email='deepa@techpanda.test',
            password='Password123!',
            role=UserRole.MARKETING,
            branch=self.branch
        )

        # Sample Lead assigned to telecaller and counselor
        self.lead = Lead.objects.create(
            name='Test Student Lead',
            phone='9876543210',
            email='student@test.com',
            assigned_telecaller=self.telecaller,
            assigned_counselor=self.counselor,
            branch=self.branch,
            assignment_status='Assigned'
        )

    def test_universal_user_leads_redirect(self):
        self.client.force_login(self.admin_user)

        # Telecaller leads route
        res = self.client.get(reverse('universal_user_leads', args=[self.telecaller.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('telecaller_leads', args=[self.telecaller.pk]), res['Location'])

        # Counselor drilldown route
        res = self.client.get(reverse('universal_user_leads', args=[self.counselor.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('admin_counselor_leads_drilldown', args=[self.counselor.pk]), res['Location'])

        # Generic role route (e.g., Sales Head)
        res = self.client.get(reverse('universal_user_leads', args=[self.sales_head.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertIn(f"/admin/leads/?assigned_to={self.sales_head.pk}", res['Location'])

    def test_universal_user_profile_redirect(self):
        self.client.force_login(self.admin_user)

        # Sales Head
        res = self.client.get(reverse('universal_user_profile', args=[self.sales_head.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('admin_manager_detail', args=[self.sales_head.pk]), res['Location'])

        # Branch Head
        res = self.client.get(reverse('universal_user_profile', args=[self.branch_head.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('admin_branch_head_detail', args=[self.branch_head.pk]), res['Location'])

        # Counselor
        res = self.client.get(reverse('universal_user_profile', args=[self.counselor.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('admin_counselor_detail', args=[self.counselor.pk]), res['Location'])

        # Telecaller
        res = self.client.get(reverse('universal_user_profile', args=[self.telecaller.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('admin_telecaller_detail', args=[self.telecaller.pk]), res['Location'])

        # Branch Admin
        res = self.client.get(reverse('universal_user_profile', args=[self.branch_admin.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('admin_branch_admin_detail', args=[self.branch_admin.pk]), res['Location'])

        # Receptionist
        res = self.client.get(reverse('universal_user_profile', args=[self.receptionist.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('admin_receptionist_detail', args=[self.receptionist.pk]), res['Location'])

        # Accountant
        res = self.client.get(reverse('universal_user_profile', args=[self.accountant.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('admin_accountant_detail', args=[self.accountant.pk]), res['Location'])

    def test_admin_user_edit_get_and_post(self):
        self.client.force_login(self.admin_user)

        # GET edit form
        url = reverse('admin_user_edit', args=[self.telecaller.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Arun')

        # POST update fields
        post_data = {
            'first_name': 'Arunkumar',
            'last_name': 'Sundar',
            'email': 'arun.updated@techpanda.test',
            'phone': '9123456780',
            'role': UserRole.TELECALLER,
            'branch': self.branch.id,
            'counselor': self.counselor.id,
            'is_active': 'on',
            'next': reverse('admin_users_list')
        }
        res = self.client.post(url, post_data)
        self.assertEqual(res.status_code, 302)

        self.telecaller.refresh_from_db()
        self.assertEqual(self.telecaller.first_name, 'Arunkumar')
        self.assertEqual(self.telecaller.last_name, 'Sundar')
        self.assertEqual(self.telecaller.email, 'arun.updated@techpanda.test')
        self.assertEqual(self.telecaller.counselor, self.counselor)

    def test_admin_user_delete_self_prevention(self):
        self.client.force_login(self.admin_user)
        url = reverse('admin_user_delete', args=[self.admin_user.pk])
        res = self.client.post(url)
        self.assertEqual(res.status_code, 302)
        # Admin user must still exist
        self.assertTrue(User.objects.filter(pk=self.admin_user.pk).exists())

    def test_admin_user_delete_safe_unassignment(self):
        self.client.force_login(self.admin_user)

        # Create FollowUp and CallHistory associated with the telecaller
        FollowUp.objects.create(
            lead=self.lead,
            telecaller=self.telecaller,
            follow_up_date=timezone.now().date(),
            status='PENDING'
        )
        CallHistory.objects.create(
            lead=self.lead,
            caller=self.telecaller,
            telecaller=self.telecaller,
            call_status='CONNECTED',
            duration=30
        )

        tc_id = self.telecaller.pk
        url = reverse('admin_user_delete', args=[tc_id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, 302)

        # Telecaller must be deleted
        self.assertFalse(User.objects.filter(pk=tc_id).exists())

        # Lead must be preserved and cleanly unassigned
        self.lead.refresh_from_db()
        self.assertIsNone(self.lead.assigned_telecaller)
        self.assertEqual(self.lead.assignment_status, 'Unassigned')
        self.assertIn("deleted", self.lead.pending_assignment_reason)

        # FollowUp and CallHistory must be preserved with null telecaller
        fu = FollowUp.objects.filter(lead=self.lead).first()
        self.assertIsNotNone(fu)
        self.assertIsNone(fu.telecaller)

        ch = CallHistory.objects.filter(lead=self.lead).first()
        self.assertIsNotNone(ch)
        self.assertIsNone(ch.caller)

    def test_admin_user_toggle_status_and_self_prevention(self):
        self.client.force_login(self.admin_user)

        # 1. Attempt to toggle own account (must be blocked)
        own_url = reverse('admin_user_toggle_status', args=[self.admin_user.pk])
        res = self.client.post(own_url)
        self.assertEqual(res.status_code, 302)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

        # 2. Deactivate active telecaller
        self.assertTrue(self.telecaller.is_active)
        tc_url = reverse('admin_user_toggle_status', args=[self.telecaller.pk])
        res = self.client.post(tc_url)
        self.assertEqual(res.status_code, 302)
        self.telecaller.refresh_from_db()
        self.assertFalse(self.telecaller.is_active)

        # 3. Reactivate telecaller
        res = self.client.post(tc_url)
        self.assertEqual(res.status_code, 302)
        self.telecaller.refresh_from_db()
        self.assertTrue(self.telecaller.is_active)

    def test_list_templates_rendering(self):
        self.client.force_login(self.admin_user)

        urls = [
            reverse('admin_users_list'),
            reverse('admin_telecallers_list'),
            reverse('admin_counselors_list'),
            reverse('admin_managers_list'),
            reverse('admin_branch_heads_list'),
            reverse('admin_branch_admins_list'),
            reverse('admin_receptionists_list'),
            reverse('admin_accountants_list'),
            reverse('admin_marketing_users_list'),
        ]

        for u in urls:
            res = self.client.get(u)
            self.assertEqual(res.status_code, 200, f"Failed rendering {u}")
            self.assertContains(res, 'Resend Invite')
            self.assertContains(res, 'Deactivate')
            self.assertContains(res, 'Edit')
            self.assertContains(res, 'Password')
            self.assertContains(res, 'Delete')
            self.assertContains(res, 'universalUserDeleteModal')
            # Verify Profile and Leads buttons are completely removed from toolbar
            self.assertNotContains(res, 'tp-action-leads')
            self.assertNotContains(res, 'tp-action-profile')
