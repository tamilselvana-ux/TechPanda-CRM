path = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\TODO.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

track_z = '''

---

## Track Z: Student Enquiry Form Format Redesign (Matches Uploaded Paper Form)

### Assumptions
- Replaces the legacy Digital Marketing questionnaire inside `CRM/templates/public/student_enquiry_form.html` with the new **Student Enquiry Form – Training & Placement** format matching the uploaded sheet (`Basic Information`, `Location & Mode`, `Education Qualifications`, `Work Experience`, `Interested Course`, `Student Reference`).
- Top-left displays the current standardized CRM brand logo (`itechpanda_logo.png` / `•t` circular emblem); top-right displays `Enquiry Form No` (auto-populated with token preview / editable reference).
- Backward-compatible custom field keys (such as `ug_degree`, `ug_year`, `course_track`) continue to populate alongside the new structured keys (`age`, `whatsapp_number`, `emergency_contact`, `preferred_training_mode`, `has_work_experience`, `company_name`, `designation`, `work_start_date`, `work_end_date`, `current_ctc`, `it_experience`, `absconded`, `has_pf_uan`, `expected_ctc`, `reason_for_leaving`, 12 IT/Training courses).

- [ ] **Item 171 — Backend Form Parsing & Lead Custom Fields Mapping**:
  - What: Update `public_student_enquiry_form` in `CRM/leads/views_walkin.py` and field extraction in `CRM/leads/detail_service.py` to accept, validate, store in `custom_fields`, and summarize in Lead notes all fields from the 6 sections of the new Training & Placement Student Enquiry Form.
  - Where: `CRM/leads/views_walkin.py`, `CRM/leads/detail_service.py`.
  - Acceptance checks: POST `/enquiry/` stores all Basic Info, Location & Mode, Education, Work Experience, Interested Courses, and Student Reference fields into `Lead.custom_fields` and formatted `notes`.
  - Status: ⬜.

- [ ] **Item 172 — New Student Enquiry Form Template Matching Uploaded Sheet**:
  - What: Rebuild `CRM/templates/public/student_enquiry_form.html` with exact layout matching the uploaded sheet: Top-left brand logo + top-right Enquiry Form No box, `Basic Information` (Date, Time, Full Name, Gender, DOB, Age auto-calc, Email, Mobile Number, Whatsapp + Same as Mobile toggle, Emergency Contact), `Location & Mode` (Current Address, Preferred Training Mode Online/Offline), `Education Qualifications` (Fresher/Experienced, Years of Experience, UG + Passed Out Year, PG + Passed Out Year, Backlogs Yes/No/Cleared Later, Highest Education), `Work Experience` (Yes/No, Company Name, Designation, Start Date, End Date, Current CTC, IT Experience, Absconded, PF/UAN ID, Expected CTC, Reason for Leaving), `Interested Course` (all 12 checkboxes + Others text box), and `Student Reference` (Number 1, Number 2). Fully responsive on 360px, 390px, 768px, 1280px.
  - Where: `CRM/templates/public/student_enquiry_form.html`.
  - Acceptance checks: All sections and checkboxes match uploaded image; mobile & desktop render without overflow; DOB auto-computes Age.
  - Status: ⬜.

- [ ] **Item 173 — Lead Detail & Success View Compatibility**:
  - What: Verify `student_enquiry_success.html` and Lead Detail screens cleanly show the submitted `Enquiry Form No` / Token, Interested Courses, Work Experience, and Reference numbers without errors.
  - Where: `CRM/templates/public/student_enquiry_success.html`, `CRM/leads/detail_service.py`.
  - Acceptance checks: Submitted details appear cleanly on success page and Lead Detail view.
  - Status: ⬜.

- [ ] **Item 174 — Browser Verification, Responsive Check & Automated Regression Tests**:
  - What: Test GET/POST on `/enquiry/` for Fresher & Experienced flows, verify existing `tests_qr_walkin_enquiry.py`, capture live Chrome desktop (1280px) & mobile (390px) screenshots checking zero horizontal scroll and console errors, run `manage.py check` and `stub_scan.py`.
  - Where: `CRM/scratch/test_new_enquiry_form.py`.
  - Acceptance checks: 100% test pass rate, 0 Django check errors, 0 stub blockers, visual match confirmed.
  - Status: ⬜.
'''

content += track_z
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully added Track Z to TODO.md")
