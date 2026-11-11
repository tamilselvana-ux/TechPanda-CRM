p = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\public\student_enquiry_form.html"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()

old_css = """    .form-wrapper {
      max-width: 820px;
      margin: 0 auto;
    }

    .form-card {
      background: var(--bg-card);
      border: 1px solid #e2e8f0;
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-card);
      padding: 32px 34px 38px;
    }"""

new_css = """    .form-wrapper {
      width: 100%;
      max-width: 820px;
      margin: 0 auto;
    }

    .form-card {
      width: 100%;
      max-width: 100%;
      overflow: hidden;
      background: var(--bg-card);
      border: 1px solid #e2e8f0;
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-card);
      padding: 32px 34px 38px;
    }"""

assert old_css in s, "old_css not found"
s = s.replace(old_css, new_css, 1)

old_group = """    .form-group {
      display: flex;
      flex-direction: column;
      gap: 5px;
    }"""

new_group = """    .form-group {
      display: flex;
      flex-direction: column;
      gap: 5px;
      min-width: 0;
      max-width: 100%;
    }"""

assert old_group in s, "old_group not found"
s = s.replace(old_group, new_group, 1)

old_media = """    @media (max-width: 720px) {
      body { padding: 12px 8px 40px; }
      .form-card { padding: 20px 16px; }
      .row-2col, .row-3col, .row-dob-age { grid-template-columns: 1fr; gap: 10px; }
      .course-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
      .header-top-row { flex-direction: column; align-items: center; text-align: center; }
      .btn-submit { width: 100%; }
    }"""

new_media = """    @media (max-width: 720px) {
      body { padding: 10px 8px 40px; }
      .form-card { padding: 18px 14px; border-radius: 12px; }
      .form-subtitle { font-size: 0.94rem; line-height: 1.35; }
      .row-2col, .row-3col, .row-dob-age { grid-template-columns: minmax(0, 1fr); gap: 10px; }
      .course-grid { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 8px; }
      .header-top-row { flex-direction: column; align-items: center; text-align: center; }
      .form-control, .form-select { max-width: 100%; min-width: 0; }
      .btn-submit { width: 100%; }
    }"""

assert old_media in s, "old_media not found"
s = s.replace(old_media, new_media, 1)

with open(p, "w", encoding="utf-8") as f:
    f.write(s)
print("Fixed mobile responsiveness CSS on student_enquiry_form.html")
