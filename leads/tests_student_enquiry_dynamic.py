from django.test import TestCase, Client
from django.urls import reverse
from leads.models import Lead, LeadCategory
from branches.models import Branch
from products.models import Product
from lead_channels.models import Channel
from accounts.models import User, UserRole
from leads.forms import AdminLeadForm, ManagerLeadCreateForm, TelecallerLeadCreateForm


class StudentEnquiryDynamicFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.branch = Branch.objects.create(name="Chennai Main", status="Active")
        self.channel = Channel.objects.create(name="Walk-in", status="Active")
        self.product = Product.objects.create(name="Python Full Stack", status="Active")
        
        self.admin = User.objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="password123",
            role=UserRole.ADMIN
        )
        self.manager = User.objects.create_user(
            username="manager_test",
            email="manager@test.com",
            password="password123",
            role=UserRole.SALES_HEAD,
            branch=self.branch
        )
        self.telecaller = User.objects.create_user(
            username="telecaller_test",
            email="telecaller@test.com",
            password="password123",
            role=UserRole.TELECALLER,
            branch=self.branch
        )

        self.valid_fresher_payload = {
            "name": "Arun Kumar",
            "phone": "9876543210",
            "email": "arun.kumar@gmail.com",
            "emergency_contact": "9840112233",
            "whatsapp_number": "9876543210",
            "branch_id": self.branch.id,
            "product_id": self.product.id,
            "preferred_training_mode": "Offline",
            "experience_type": "Fresher",
            "ug_qualification": "B.Tech CSE",
            "ug_passed_out_year": "2024",
            "pg_qualification": "",
            "pg_passed_out_year": "",
            "backlogs": "Yes",
            "highest_education": "B.Tech",
            "interested_course": ["Python Full Stack"],
        }

        self.valid_experienced_payload = {
            "name": "Priya Sharma",
            "phone": "9876500000",
            "email": "priya.sharma@gmail.com",
            "emergency_contact": "9840998877",
            "whatsapp_number": "9876500000",
            "branch_id": self.branch.id,
            "product_id": self.product.id,
            "preferred_training_mode": "Offline",
            "experience_type": "Experienced",
            "years_of_experience": "2.5 Years",
            "ug_qualification": "B.E ECE",
            "ug_passed_out_year": "2021",
            "highest_education": "B.E",
            "company_name": "Infosys",
            "designation": "Systems Engineer",
            "current_ctc": "4.2 LPA",
            "expected_ctc": "6.5 LPA",
            "it_experience": "Yes",
            "absconded": "No",
            "has_pf_uan": "Yes",
            "interested_course": ["Python Full Stack"],
        }

    def test_missing_email_rejected(self):
        payload = dict(self.valid_fresher_payload)
        payload["email"] = ""
        resp = self.client.post(reverse("public_student_enquiry_form"), payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Please enter your Email address.", resp.content.decode("utf-8"))

    def test_invalid_email_format_rejected(self):
        payload = dict(self.valid_fresher_payload)
        payload["email"] = "not-an-email"
        resp = self.client.post(reverse("public_student_enquiry_form"), payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Please enter a valid Email address.", resp.content.decode("utf-8"))

    def test_missing_emergency_contact_rejected(self):
        payload = dict(self.valid_fresher_payload)
        payload["emergency_contact"] = ""
        resp = self.client.post(reverse("public_student_enquiry_form"), payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Please enter an Emergency Contact Number", resp.content.decode("utf-8"))

    def test_invalid_emergency_contact_digits_rejected(self):
        payload = dict(self.valid_fresher_payload)
        payload["emergency_contact"] = "12345"
        resp = self.client.post(reverse("public_student_enquiry_form"), payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Please enter a valid 10-digit Emergency Contact Number", resp.content.decode("utf-8"))

    def test_fresher_submission_saves_clean_profile(self):
        resp = self.client.post(reverse("public_student_enquiry_form"), self.valid_fresher_payload)
        self.assertEqual(resp.status_code, 200)
        
        lead = Lead.objects.get(phone="9876543210")
        self.assertEqual(lead.name, "Arun Kumar")
        self.assertEqual(lead.email, "arun.kumar@gmail.com")
        self.assertEqual(lead.alternate_phone, "9840112233")
        self.assertEqual(lead.custom_fields.get("emergency_contact"), "9840112233")
        self.assertEqual(lead.custom_fields.get("experience_type"), "Fresher")
        self.assertEqual(lead.custom_fields.get("years_of_experience"), "0 Years")
        self.assertEqual(lead.custom_fields.get("has_work_experience"), "No")
        self.assertEqual(lead.custom_fields.get("backlogs"), "Yes")
        self.assertEqual(lead.custom_fields.get("ug_qualification"), "B.Tech CSE")
        self.assertEqual(lead.custom_fields.get("company_name"), "")

    def test_experienced_submission_saves_work_experience(self):
        resp = self.client.post(reverse("public_student_enquiry_form"), self.valid_experienced_payload)
        self.assertEqual(resp.status_code, 200)

        lead = Lead.objects.get(phone="9876500000")
        self.assertEqual(lead.name, "Priya Sharma")
        self.assertEqual(lead.email, "priya.sharma@gmail.com")
        self.assertEqual(lead.alternate_phone, "9840998877")
        self.assertEqual(lead.custom_fields.get("emergency_contact"), "9840998877")
        self.assertEqual(lead.custom_fields.get("experience_type"), "Experienced")
        self.assertEqual(lead.custom_fields.get("years_of_experience"), "2.5 Years")
        self.assertEqual(lead.custom_fields.get("has_work_experience"), "Yes")
        self.assertEqual(lead.custom_fields.get("company_name"), "Infosys")
        self.assertEqual(lead.custom_fields.get("designation"), "Systems Engineer")
        self.assertEqual(lead.custom_fields.get("current_ctc"), "4.2 LPA")

    def test_internal_lead_forms_require_email(self):
        # AdminLeadForm
        admin_form = AdminLeadForm(data={
            "name": "Test Lead",
            "phone": "9998887770",
            "email": "",
            "category": LeadCategory.TRAINING,
            "status": "New",
        })
        self.assertFalse(admin_form.is_valid())
        self.assertIn("email", admin_form.errors)

        # ManagerLeadCreateForm
        mgr_form = ManagerLeadCreateForm(manager=self.manager, data={
            "name": "Test Lead 2",
            "phone": "9998887771",
            "email": "",
            "category": LeadCategory.TRAINING,
            "status": "New",
        })
        self.assertFalse(mgr_form.is_valid())
        self.assertIn("email", mgr_form.errors)

        # TelecallerLeadCreateForm
        tc_form = TelecallerLeadCreateForm(data={
            "name": "Test Lead 3",
            "phone": "9998887772",
            "email": "",
            "category": LeadCategory.TRAINING,
            "status": "New",
        })
        self.assertFalse(tc_form.is_valid())
        self.assertIn("email", tc_form.errors)
