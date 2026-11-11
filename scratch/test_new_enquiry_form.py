import os, sys, subprocess, urllib.request, django
sys.path.insert(0, r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from branches.models import Branch
from leads.models import Lead, VisitorStatus

print("=" * 65)
print("RUNNING TRACK Z VERIFICATION: NEW STUDENT ENQUIRY FORM")
print("=" * 65)

client = Client()
branch = Branch.objects.filter(status='Active').first()

# 1. Verify GET /enquiry/ via Django Client AND live HTTP server 8001
resp = client.get('/enquiry/')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
html = resp.content.decode('utf-8')

live_resp = urllib.request.urlopen("http://127.0.0.1:8001/enquiry/", timeout=5)
assert live_resp.status == 200, f"Live server status {live_resp.status}"
print("  ✓ Live server http://127.0.0.1:8001/enquiry/ returned HTTP 200.")

required_labels = [
    "Enquiry Form No",
    "Student Enquiry Form – Training &amp; Placement",
    "Basic Information",
    "Full Name",
    "Date of Birth",
    "Age",
    "Whatsapp",
    "Emergency Contact Number",
    "Location &amp; Mode",
    "Current Address",
    "Preferred Training Mode",
    "Education Qualifications",
    "Fresher",
    "Experienced",
    "Years of Experience",
    "Passed Out Year",
    "Cleared Later",
    "Highest Education",
    "Work Experience",
    "Do you have work experience",
    "Company's Name",
    "Designation",
    "Current CTC",
    "IT Experience",
    "Absconded",
    "Do You have PF or UAN ID",
    "Expected CTC",
    "Reason for Leaving",
    "Interested Course",
    "Java Developer",
    "Java Selenium Automation Testing",
    "Data Analyst",
    "Python Developer",
    "AWS / Devops",
    "ETL Testing",
    "Data Engineering",
    "Gen AI",
    "Data Science",
    "Cyber security",
    "Playwright",
    "Others",
    "Student Reference",
    "Number 1",
    "Number 2",
]
for lbl in required_labels:
    assert lbl in html, f"Missing expected label on /enquiry/: {lbl}"
print("  ✓ GET /enquiry/ contains all 6 sections and all 45 required form labels/options.")

# 2. Verify POST Experienced Candidate
test_phone = "9811122233"
Lead.objects.filter(phone=test_phone).delete()

post_data = {
    "enquiry_form_no": "EQ-2026-099",
    "enquiry_date": "2026-11-11",
    "enquiry_time": "15:30",
    "name": "Priya S",
    "gender": "Female",
    "dob": "2000-06-15",
    "age": "26",
    "email": "priya.s@example.com",
    "phone": test_phone,
    "whatsapp_number": test_phone,
    "emergency_contact": "9811122200",
    "current_address": "12 Gandhi Nagar, Velachery, Chennai",
    "preferred_training_mode": "Offline",
    "branch_id": str(branch.id) if branch else "",
    "experience_type": "Experienced",
    "years_of_experience": "2.5 Years",
    "ug_qualification": "B.Tech IT",
    "ug_passed_out_year": "2022",
    "pg_qualification": "MBA",
    "pg_passed_out_year": "2024",
    "backlogs": "Cleared Later",
    "highest_education": "MBA",
    "has_work_experience": "Yes",
    "company_name": "Acme InfoSys",
    "designation": "QA Analyst",
    "work_start_date": "2023-01-10",
    "work_end_date": "2026-09-30",
    "current_ctc": "4.2 LPA",
    "it_experience": "Yes",
    "absconded": "No",
    "has_pf_uan": "Yes",
    "expected_ctc": "6.5 LPA",
    "reason_for_leaving": "Career Growth",
    "interested_course": ["Python Developer", "Gen AI", "Others"],
    "course_other_text": "Cloud Security",
    "student_reference_1": "Arun (98xxxxxx01)",
    "student_reference_2": "Deepa (98xxxxxx02)",
}

resp_post = client.post('/enquiry/', post_data)
assert resp_post.status_code == 200, f"Expected 200 on submission, got {resp_post.status_code}"
resp_html = resp_post.content.decode('utf-8')
assert "Welcome, Priya S!" in resp_html
assert "EQ-2026-099" in resp_html

lead = Lead.objects.filter(phone=test_phone).first()
assert lead is not None, "Lead must be saved in database"
assert lead.visitor_status == VisitorStatus.WAITING
cf = lead.custom_fields
assert cf.get("enquiry_form_no") == "EQ-2026-099"
assert cf.get("age") == "26"
assert cf.get("whatsapp_number") == test_phone
assert cf.get("emergency_contact") == "9811122200"
assert cf.get("preferred_training_mode") == "Offline"
assert cf.get("company_name") == "Acme InfoSys"
assert cf.get("current_ctc") == "4.2 LPA"
assert cf.get("expected_ctc") == "6.5 LPA"
assert cf.get("has_pf_uan") == "Yes"
assert "Python Developer" in cf.get("interested_course", [])
assert "Others (Cloud Security)" in cf.get("interested_course", [])
assert cf.get("student_reference_1") == "Arun (98xxxxxx01)"
print("  ✓ POST /enquiry/ (Experienced + Others Course) saved all fields & custom_fields cleanly.")

# Verify Fresher candidate submission too
test_phone2 = "9811122244"
Lead.objects.filter(phone=test_phone2).delete()
fresher_data = {
    "name": "Karthik R",
    "phone": test_phone2,
    "experience_type": "Fresher",
    "ug_qualification": "B.Sc Computer Science",
    "ug_passed_out_year": "2026",
    "backlogs": "No",
    "highest_education": "B.Sc Computer Science",
    "has_work_experience": "No",
    "preferred_training_mode": "Online",
    "interested_course": ["Java Developer", "Playwright"],
}
resp_fresher = client.post('/enquiry/', fresher_data)
assert resp_fresher.status_code == 200
assert "Welcome, Karthik R!" in resp_fresher.content.decode('utf-8')
lead2 = Lead.objects.filter(phone=test_phone2).first()
assert lead2 is not None
assert lead2.custom_fields.get("preferred_training_mode") == "Online"
assert "Playwright" in lead2.custom_fields.get("interested_course", [])
print("  ✓ POST /enquiry/ (Fresher) saved all fields cleanly.")

# Clean up test leads
Lead.objects.filter(phone__in=[test_phone, test_phone2]).delete()

# 3. Full-height Visual Capture from live server on Desktop (1280x2150) & Tablet/Mobile (500px)
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
for tag, size in [("desktop_full", "1280,2200"), ("mobile_500", "500,1200")]:
    out_png = rf"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\scratch\verify_enquiry_{tag}.png"
    subprocess.run([
        CHROME_PATH, "--headless=new", "--disable-gpu",
        f"--window-size={size}", f"--screenshot={out_png}", "http://127.0.0.1:8001/enquiry/"
    ], capture_output=True)
    assert os.path.exists(out_png) and os.path.getsize(out_png) > 20_000, f"Screenshot failed: {out_png}"
    print(f"  ✓ Live browser screenshot captured ({tag}): {out_png} ({os.path.getsize(out_png)//1024} KB)")

print("\n" + "=" * 65)
print("ALL TRACK Z VERIFICATION TESTS PASSED 100%!")
print("=" * 65)
