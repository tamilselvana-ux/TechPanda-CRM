import os
import re
import glob
import subprocess
import markdown

PROJECT_ROOT = r"d:\CRM_Integrated_v2\CRM_Integrated_v2"
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
SOPS_DIR = os.path.join(DOCS_DIR, "sops")
ASSETS_DIR = os.path.join(DOCS_DIR, "assets")
PDF_DIR = os.path.join(DOCS_DIR, "pdf")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

os.makedirs(PDF_DIR, exist_ok=True)

CSS_STYLES = """
@page {
    size: A4;
    margin: 18mm 14mm 18mm 14mm;
    @top-left {
        content: "iTechPanda CRM — Official Documentation";
        font-family: 'Segoe UI', sans-serif;
        font-size: 7.5pt;
        color: #64748b;
    }
    @top-right {
        content: "Confidential · v2.4.0";
        font-family: 'Segoe UI', sans-serif;
        font-size: 7.5pt;
        color: #64748b;
    }
    @bottom-left {
        content: "https://itechpandacrm.in";
        font-family: 'Segoe UI', sans-serif;
        font-size: 7.5pt;
        color: #64748b;
    }
    @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
        font-family: 'Segoe UI', sans-serif;
        font-size: 7.5pt;
        color: #475569;
        font-weight: 600;
    }
}
@page :first {
    @top-left { content: none; }
    @top-right { content: none; }
    @bottom-left { content: none; }
    @bottom-right { content: none; }
}

body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.55;
    color: #1e293b;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
}

/* Cover Page */
.cover-page {
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 82vh;
    text-align: center;
    padding: 36px 24px;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.cover-logo {
    width: 112px;
    height: 112px;
    object-fit: contain;
    margin-bottom: 24px;
    border: none !important;
    box-shadow: none !important;
}

.cover-badge {
    display: inline-block;
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 9999px;
    padding: 5px 16px;
    font-size: 8.5pt;
    font-weight: 700;
    letter-spacing: 0.06em;
    color: #174b89;
    margin-bottom: 18px;
}

.cover-title {
    font-size: 26pt;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 10px 0;
}

.cover-subtitle {
    font-size: 13.5pt;
    font-weight: 600;
    color: #174b89;
    margin: 0 0 28px 0;
    max-width: 520px;
}

.cover-meta {
    font-size: 9.5pt;
    color: #475569;
    margin-top: 28px;
    line-height: 1.85;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 16px 28px;
    border-radius: 10px;
}

/* Headings */
h1 {
    font-size: 17pt;
    font-weight: 800;
    color: #0f172a;
    border-bottom: 2.5px solid #174b89;
    padding-bottom: 6px;
    margin-top: 24px;
    margin-bottom: 12px;
    page-break-after: avoid;
}

.sop-break h1:first-child {
    page-break-before: always;
}

h2 {
    font-size: 13pt;
    font-weight: 700;
    color: #174b89;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4px;
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
}

h3 {
    font-size: 11pt;
    font-weight: 700;
    color: #0369a1;
    margin-top: 14px;
    margin-bottom: 6px;
    page-break-after: avoid;
}

p {
    margin: 0 0 8px 0;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 16px 0;
    font-size: 8.6pt;
    page-break-inside: auto;
}

thead {
    display: table-header-group;
}

tr {
    page-break-inside: avoid;
}

th {
    background-color: #174b89;
    color: #ffffff;
    font-weight: 600;
    text-align: left;
    padding: 7px 9px;
    border: 1px solid #174b89;
}

td {
    padding: 6px 9px;
    border: 1px solid #cbd5e1;
    vertical-align: top;
    word-break: break-word;
}

tr:nth-child(even) {
    background-color: #f8fafc;
}

/* Images & Figures */
figure {
    margin: 12px 0 16px 0;
    text-align: center;
    page-break-inside: avoid;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px;
}

figure img {
    max-width: 98%;
    max-height: 310px;
    height: auto;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    background-color: #ffffff;
}

figcaption {
    font-size: 8.5pt;
    font-weight: 600;
    color: #475569;
    margin-top: 6px;
}

/* Screenshot Placeholder Callout */
.screenshot-placeholder {
    border: 1.5px dashed #0284c7;
    background-color: #f0f9ff;
    color: #0369a1;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 9pt;
    font-weight: 600;
    margin: 10px 0;
    page-break-inside: avoid;
}

/* TO CONFIRM Highlight */
.to-confirm-box {
    border-left: 4px solid #d97706;
    background-color: #fffbeb;
    color: #92400e;
    padding: 8px 12px;
    border-radius: 0 6px 6px 0;
    margin: 8px 0;
    font-size: 9.2pt;
}

/* Blockquotes & Code */
blockquote {
    border-left: 4px solid #174b89;
    background-color: #f1f5f9;
    padding: 8px 12px;
    margin: 10px 0 14px 0;
    border-radius: 0 6px 6px 0;
    font-size: 9.2pt;
    color: #334155;
}

code {
    font-family: Consolas, "Courier New", monospace;
    font-size: 8.6pt;
    background-color: #f1f5f9;
    color: #0f172a;
    padding: 1px 4px;
    border-radius: 4px;
    word-break: break-word;
}

pre {
    background-color: #0f172a;
    color: #f8fafc;
    padding: 10px 12px;
    border-radius: 6px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 8.2pt;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 10px 0 14px 0;
    page-break-inside: avoid;
}

ul, ol {
    margin: 0 0 10px 0;
    padding-left: 20px;
}

li {
    margin-bottom: 4px;
}

.sop-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 10px;
    margin-bottom: 14px;
}

.sop-banner img {
    width: 36px;
    height: 36px;
    object-fit: contain;
}

.sop-banner-label {
    font-size: 8.5pt;
    font-weight: 700;
    color: #174b89;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
"""

def preprocess_markdown(md_text, base_dir):
    # Convert markdown images to local file:/// <figure> tags
    def img_replacer(match):
        caption = match.group(1)
        rel_path = match.group(2)
        abs_img = os.path.normpath(os.path.join(base_dir, rel_path))
        if not os.path.exists(abs_img):
            return f'<div class="screenshot-placeholder">[IMAGE MISSING: {caption} ({rel_path})]</div>'
        uri = f"file:///{abs_img.replace(os.sep, '/')}"
        return f'<figure><img src="{uri}" alt="{caption}"><figcaption>{caption}</figcaption></figure>'

    md_text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', img_replacer, md_text)

    # Style [SCREENSHOT: ...] placeholders
    def scr_replacer(match):
        txt = match.group(1)
        return f'<div class="screenshot-placeholder">📸 SCREENSHOT NEEDED: {txt}</div>'
    md_text = re.sub(r'\[SCREENSHOT:\s*([^\]]+)\]', scr_replacer, md_text)

    # Format tick boxes nicely
    md_text = md_text.replace('- [ ] ', '- &#9744; ')
    md_text = md_text.replace('- [x] ', '- &#9745; ')

    # Strip file:/// markdown links to clean bold text
    md_text = re.sub(r'\[([^\]]+)\]\(file:///[^)]+\)', r'**\1**', md_text)

    md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    html = md.convert(md_text)

    # Highlight TO CONFIRM paragraphs cleanly
    html = re.sub(
        r'(<(?:p|li)>.*?⚠ TO CONFIRM.*?</(?:p|li)>)',
        lambda m: m.group(0).replace('⚠ TO CONFIRM', '<span style="background:#fef3c7;color:#92400e;font-weight:700;padding:1px 5px;border-radius:4px;">⚠ TO CONFIRM</span>'),
        html
    )
    return html

def build_pdf_from_html(html_content, output_pdf, header_title):
    temp_html = os.path.join(PDF_DIR, "_tmp_pdf_render.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    header_template = f"<div style='font-size:7.8pt;color:#64748b;margin-left:15mm;width:100%;font-family:sans-serif;'>{header_title}</div>"
    footer_template = "<div style='font-size:7.8pt;color:#64748b;margin-right:15mm;width:100%;text-align:right;font-family:sans-serif;'>Page <span class='pageNumber'></span> of <span class='totalPages'></span></div>"

    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf}",
        temp_html
    ]
    subprocess.run(cmd, capture_output=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)

    if os.path.exists(output_pdf):
        size_kb = os.path.getsize(output_pdf) / 1024
        print(f"  [PDF OK] {os.path.basename(output_pdf)} ({size_kb:.1f} KB)")
        return True
    else:
        print(f"  [ERROR] Failed to generate {output_pdf}")
        return False

def build_project_document_pdf():
    print("\n1. Building 01_Project_Document.pdf ...")
    md_path = os.path.join(DOCS_DIR, "01_Project_Document.md")
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    logo_uri = f"file:///{os.path.join(ASSETS_DIR, 'logo.png').replace(os.sep, '/')}"
    cover_html = f"""
    <div class="cover-page">
      <img src="{logo_uri}" class="cover-logo" alt="Logo">
      <div class="cover-badge">OFFICIAL SYSTEM &amp; OPERATIONS MANUAL</div>
      <div class="cover-title">iTechPanda / DigiPanda CRM</div>
      <div class="cover-subtitle">Complete Project Documentation, Workflows, Roles &amp; Architecture</div>
      <div class="cover-meta">
        <strong>Version:</strong> v2.4.0 (`CRM_Integrated_v2`)<br>
        <strong>Effective Date:</strong> 10 November 2026<br>
        <strong>Deployment Domain:</strong> itechpandacrm.in<br>
        <strong>Prepared For:</strong> Counselors, Telecallers, Receptionists, Branch Heads, Accounts, Admin &amp; Engineering
      </div>
    </div>
    """
    body_html = preprocess_markdown(md_text, DOCS_DIR)
    full_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>iTechPanda CRM — Project Document</title><style>{CSS_STYLES}</style></head>
<body>{cover_html}{body_html}</body></html>"""

    out_pdf = os.path.join(PDF_DIR, "01_Project_Document.pdf")
    build_pdf_from_html(full_html, out_pdf, "iTechPanda CRM | Complete Project Document (v2.4.0)")

def build_individual_sop_pdfs():
    print("\n2. Building Individual SOP PDFs & SOP Index PDF...")
    logo_uri = f"file:///{os.path.join(ASSETS_DIR, 'logo.png').replace(os.sep, '/')}"
    md_files = sorted(glob.glob(os.path.join(SOPS_DIR, "*.md")))

    for fpath in md_files:
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            md_text = f.read()

        body_html = preprocess_markdown(md_text, SOPS_DIR)
        banner_html = f"""
        <div class="sop-banner">
          <div style="display:flex;align-items:center;gap:10px;">
            <img src="{logo_uri}" alt="Logo">
            <span class="sop-banner-label">iTechPanda CRM · Standard Operating Procedure</span>
          </div>
          <span style="font-size:8pt;color:#64748b;">v2.0 · 10 Nov 2026</span>
        </div>
        """
        full_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{fname}</title><style>{CSS_STYLES}</style></head>
<body>{banner_html}{body_html}</body></html>"""

        pdf_name = fname.replace(".md", ".pdf")
        out_pdf = os.path.join(PDF_DIR, pdf_name)
        build_pdf_from_html(full_html, out_pdf, f"iTechPanda CRM | {fname.replace('.md', '')}")

def build_combined_sop_manual_pdf():
    print("\n3. Building Combined Complete SOP Manual PDF...")
    logo_uri = f"file:///{os.path.join(ASSETS_DIR, 'logo.png').replace(os.sep, '/')}"
    cover_html = f"""
    <div class="cover-page">
      <img src="{logo_uri}" class="cover-logo" alt="Logo">
      <div class="cover-badge">STANDARD OPERATING PROCEDURES MANUAL</div>
      <div class="cover-title">iTechPanda / DigiPanda CRM</div>
      <div class="cover-subtitle">Complete Operations Handbook for Staff, Management, Accounts &amp; IT (SOP-01 to SOP-24)</div>
      <div class="cover-meta">
        <strong>Document Scope:</strong> Telecaller, Counselor, Receptionist, Branch Head, Accountant, Finance &amp; Admin<br>
        <strong>Version:</strong> 2.0 · <strong>Date:</strong> 10 November 2026<br>
        <strong>Platform:</strong> https://itechpandacrm.in
      </div>
    </div>
    """

    md_files = sorted(glob.glob(os.path.join(SOPS_DIR, "*.md")))
    sections = []
    for idx, fpath in enumerate(md_files):
        with open(fpath, "r", encoding="utf-8") as f:
            md_text = f.read()
        body_html = preprocess_markdown(md_text, SOPS_DIR)
        cls = "sop-break" if idx > 0 else ""
        sections.append(f'<div class="{cls}">{body_html}</div>')

    full_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>iTechPanda CRM — Complete SOP Manual</title><style>{CSS_STYLES}</style></head>
<body>{cover_html}{''.join(sections)}</body></html>"""

    out_pdf = os.path.join(PDF_DIR, "SOP_Manual_All_Roles_Complete.pdf")
    build_pdf_from_html(full_html, out_pdf, "iTechPanda CRM | Complete SOP Manual (SOP-01 to SOP-24)")

if __name__ == "__main__":
    build_project_document_pdf()
    build_individual_sop_pdfs()
    build_combined_sop_manual_pdf()
    print("\nALL V2.0 PDF BUILDS COMPLETED!")
