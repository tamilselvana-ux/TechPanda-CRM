import os
import re
import glob
import subprocess
import markdown

PROJECT_ROOT = r"d:\CRM_Integrated_v2\CRM_Integrated_v2"
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
PROJECT_DOCS_DIR = os.path.join(DOCS_DIR, "project")
SOPS_DIR = os.path.join(DOCS_DIR, "sops")
ASSETS_DIR = os.path.join(DOCS_DIR, "assets")
PDF_DIR = os.path.join(DOCS_DIR, "pdf")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

os.makedirs(PDF_DIR, exist_ok=True)

CSS_STYLES = """
@page {
    size: A4;
    margin: 22mm 16mm 22mm 16mm;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
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
    min-height: 85vh;
    text-align: center;
    padding: 40px 20px;
}

.cover-logo {
    width: 140px;
    height: auto;
    margin-bottom: 30px;
}

.cover-title {
    font-size: 26pt;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 12px 0;
    letter-spacing: -0.5px;
}

.cover-subtitle {
    font-size: 14pt;
    font-weight: 500;
    color: #0284c7;
    margin: 0 0 30px 0;
}

.cover-meta {
    font-size: 10pt;
    color: #64748b;
    margin-top: 40px;
    line-height: 1.8;
}

.cover-badge {
    display: inline-block;
    background-color: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 9999px;
    padding: 4px 14px;
    font-size: 9pt;
    font-weight: 600;
    color: #334155;
    margin-bottom: 25px;
}

/* Headings */
h1 {
    font-size: 19pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 2px solid #0284c7;
    padding-bottom: 6px;
    margin-top: 32px;
    margin-bottom: 14px;
    page-break-before: always;
}

.cover-page + h1, .no-break-h1 {
    page-break-before: avoid !important;
}

h2 {
    font-size: 14pt;
    font-weight: 700;
    color: #1e3a8a;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4px;
    margin-top: 24px;
    margin-bottom: 10px;
    page-break-after: avoid;
}

h3 {
    font-size: 11.5pt;
    font-weight: 600;
    color: #0369a1;
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
}

h4 {
    font-size: 10.5pt;
    font-weight: 600;
    color: #334155;
    margin-top: 14px;
    margin-bottom: 6px;
}

/* Paragraphs & Text */
p {
    margin: 0 0 10px 0;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0 18px 0;
    font-size: 9pt;
    page-break-inside: avoid;
}

th {
    background-color: #1e3a8a;
    color: #ffffff;
    font-weight: 600;
    text-align: left;
    padding: 8px 10px;
    border: 1px solid #1e3a8a;
}

td {
    padding: 7px 10px;
    border: 1px solid #e2e8f0;
    vertical-align: top;
}

tr:nth-child(even) {
    background-color: #f8fafc;
}

/* Code Blocks */
pre {
    background-color: #0f172a;
    color: #f8fafc;
    padding: 12px 14px;
    border-radius: 6px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 8.5pt;
    line-height: 1.45;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 12px 0 16px 0;
    page-break-inside: avoid;
}

code {
    font-family: Consolas, "Courier New", monospace;
    font-size: 9pt;
    background-color: #f1f5f9;
    color: #0f172a;
    padding: 2px 4px;
    border-radius: 4px;
}

pre code {
    background-color: transparent;
    color: inherit;
    padding: 0;
}

/* Images & Captions */
figure {
    margin: 18px 0;
    text-align: center;
    page-break-inside: avoid;
}

img {
    max-width: 95%;
    max-height: 480px;
    height: auto;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    background-color: #ffffff;
}

figcaption {
    font-size: 8.5pt;
    font-style: italic;
    color: #64748b;
    margin-top: 6px;
}

/* Blockquotes & Alerts */
blockquote {
    border-left: 4px solid #0284c7;
    background-color: #f0f9ff;
    padding: 10px 14px;
    margin: 12px 0 16px 0;
    border-radius: 0 4px 4px 0;
    font-size: 9.5pt;
    color: #0369a1;
}

blockquote p {
    margin: 0;
}

/* Lists */
ul, ol {
    margin: 0 0 12px 0;
    padding-left: 22px;
}

li {
    margin-bottom: 4px;
}

/* Table of Contents */
.toc-container {
    page-break-after: always;
    padding: 20px 0;
}

.toc-title {
    font-size: 16pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 2px solid #0284c7;
    padding-bottom: 6px;
    margin-bottom: 16px;
}

.toc-list {
    list-style-type: none;
    padding-left: 0;
}

.toc-item {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px dotted #cbd5e1;
    font-size: 10pt;
}

.toc-item-title {
    font-weight: 600;
    color: #1e3a8a;
}
"""

def md_to_html_body(md_text, base_path):
    # Transform Markdown image syntax ![Caption](path) into <figure><img src="file:///..."><figcaption>Caption</figcaption></figure>
    def img_replacer(match):
        caption = match.group(1)
        rel_path = match.group(2)
        # resolve relative to base_path
        abs_img = os.path.normpath(os.path.join(base_path, rel_path))
        uri = f"file:///{abs_img.replace(os.sep, '/')}"
        return f'<figure><img src="{uri}" alt="{caption}"><figcaption>{caption}</figcaption></figure>'

    md_text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', img_replacer, md_text)
    
    # Transform file:// links in text to clean bold text
    md_text = re.sub(r'\[([^\]]+)\]\(file:///[^)]+\)', r'**\1**', md_text)

    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'attr_list'])
    html = md.convert(md_text)
    return html

def build_pdf_from_html(html_content, output_pdf, header_title):
    temp_html = os.path.join(PDF_DIR, "temp_render.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    header_template = f"<div style='font-size:8pt;color:#64748b;margin-left:16mm;width:100%;font-family:sans-serif;'>{header_title}</div>"
    footer_template = "<div style='font-size:8pt;color:#64748b;margin-right:16mm;width:100%;text-align:right;font-family:sans-serif;'>Page <span class='pageNumber'></span> of <span class='totalPages'></span></div>"

    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        f"--print-to-pdf={output_pdf}",
        "--display-header-footer",
        f"--header-template={header_template}",
        f"--footer-template={footer_template}",
        temp_html
    ]
    subprocess.run(cmd, capture_output=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)
    
    if os.path.exists(output_pdf):
        size_kb = os.path.getsize(output_pdf) / 1024
        print(f"  [CREATED] {os.path.basename(output_pdf)} ({size_kb:.1f} KB)")
        return True
    else:
        print(f"  [ERROR] Failed to create {output_pdf}")
        return False

def compile_project_documentation():
    print("Compiling Master Project Documentation PDF...")
    logo_path = os.path.join(ASSETS_DIR, "logo.png").replace(os.sep, "/")
    logo_uri = f"file:///{logo_path}"

    cover_html = f"""
    <div class="cover-page">
        <img src="{logo_uri}" class="cover-logo" alt="Logo">
        <div class="cover-badge">ENTERPRISE SYSTEM DOCUMENTATION</div>
        <div class="cover-title">iTechPanda CRM</div>
        <div class="cover-subtitle">Complete Architecture, Technical Specification & Operations Manual</div>
        <div class="cover-meta">
            <strong>System Version:</strong> v2.4.0 (Enterprise Release)<br>
            <strong>Target Deployment:</strong> itechpandacrm.in<br>
            <strong>Runtime Stack:</strong> Python 3.13 / Django 5.1.15 / MySQL 8.0 / Daphne ASGI<br>
            <strong>Date:</strong> November 2026<br>
            <strong>Author:</strong> Senior Software Architecture & DevOps Team
        </div>
    </div>
    """

    # Table of contents list
    project_files = sorted(glob.glob(os.path.join(PROJECT_DOCS_DIR, "*.md")))
    toc_items = []
    body_sections = []

    for fpath in project_files:
        base = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        # extract first heading
        match = re.search(r'^#\s+(.+)$', content, re.M)
        title = match.group(1) if match else base
        toc_items.append(f'<li class="toc-item"><span class="toc-item-title">{title}</span></li>')

        # Convert body
        body_html = md_to_html_body(content, PROJECT_DOCS_DIR)
        body_sections.append(body_html)

    toc_html = f"""
    <div class="toc-container">
        <div class="toc-title">Table of Contents</div>
        <ul class="toc-list">
            {''.join(toc_items)}
        </ul>
    </div>
    """

    full_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>iTechPanda CRM - Project Documentation</title>
        <style>{CSS_STYLES}</style>
    </head>
    <body>
        {cover_html}
        {toc_html}
        {''.join(body_sections)}
    </body>
    </html>
    """

    output_pdf = os.path.join(PDF_DIR, "Project_Documentation.pdf")
    build_pdf_from_html(full_html, output_pdf, "iTechPanda CRM | Master Project Documentation")

def compile_individual_sops():
    print("Compiling Individual SOP PDFs...")
    logo_path = os.path.join(ASSETS_DIR, "logo.png").replace(os.sep, "/")
    logo_uri = f"file:///{logo_path}"

    sop_files = sorted(glob.glob(os.path.join(SOPS_DIR, "*.md")))
    for fpath in sop_files:
        fname = os.path.basename(fpath).replace(".md", "")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.search(r'\*\*SOP ID\*\*:\s*([^\n\r]+)', content)
        sop_id = match.group(1).strip() if match else fname

        title_match = re.search(r'^#\s+(.+)$', content, re.M)
        title = title_match.group(1).strip() if title_match else fname

        # Convert body
        body_html = md_to_html_body(content, SOPS_DIR)

        sop_html = f"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{sop_id}: {title}</title>
            <style>
                {CSS_STYLES}
                h1 {{ page-break-before: avoid !important; }}
            </style>
        </head>
        <body>
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #0284c7; padding-bottom: 12px; margin-bottom: 20px;">
                <img src="{logo_uri}" style="height:45px; width:auto; border:none; box-shadow:none;" alt="Logo">
                <div style="text-align:right;">
                    <div style="font-size:12pt; font-weight:700; color:#0f172a;">STANDARD OPERATING PROCEDURE</div>
                    <div style="font-size:9pt; color:#64748b;">iTechPanda CRM Operations Framework</div>
                </div>
            </div>
            {body_html}
        </body>
        </html>
        """

        output_pdf = os.path.join(PDF_DIR, f"{fname.replace('-', '_')}.pdf")
        build_pdf_from_html(sop_html, output_pdf, f"iTechPanda CRM | {sop_id}")

def compile_combined_sop_manual():
    print("Compiling Complete SOP Manual PDF...")
    logo_path = os.path.join(ASSETS_DIR, "logo.png").replace(os.sep, "/")
    logo_uri = f"file:///{logo_path}"

    cover_html = f"""
    <div class="cover-page">
        <img src="{logo_uri}" class="cover-logo" alt="Logo">
        <div class="cover-badge">STANDARD OPERATING PROCEDURES MANUAL</div>
        <div class="cover-title">iTechPanda CRM</div>
        <div class="cover-subtitle">Standard Operating Procedures Manual (SOP-01 to SOP-10)</div>
        <div class="cover-meta">
            <strong>Document Set:</strong> Engineering, DevOps, Governance & Emergency Protocols<br>
            <strong>Effective Date:</strong> November 2026<br>
            <strong>System:</strong> itechpandacrm.in (v2.4.0)<br>
            <strong>Classification:</strong> Internal Operations / Confidential
        </div>
    </div>
    """

    sop_files = sorted(glob.glob(os.path.join(SOPS_DIR, "*.md")))
    toc_items = []
    body_sections = []

    for fpath in sop_files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.search(r'\*\*SOP ID\*\*:\s*([^\n\r]+)', content)
        sop_id = match.group(1).strip() if match else ""

        title_match = re.search(r'^#\s+(.+)$', content, re.M)
        title = title_match.group(1).strip() if title_match else ""

        toc_items.append(f'<li class="toc-item"><span class="toc-item-title">{sop_id}: {title}</span></li>')
        body_html = md_to_html_body(content, SOPS_DIR)
        body_sections.append(body_html)

    toc_html = f"""
    <div class="toc-container">
        <div class="toc-title">SOP Manual Directory</div>
        <ul class="toc-list">
            {''.join(toc_items)}
        </ul>
    </div>
    """

    full_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>iTechPanda CRM - Standard Operating Procedures Manual</title>
        <style>{CSS_STYLES}</style>
    </head>
    <body>
        {cover_html}
        {toc_html}
        {''.join(body_sections)}
    </body>
    </html>
    """

    output_pdf = os.path.join(PDF_DIR, "SOP_Manual_Complete.pdf")
    build_pdf_from_html(full_html, output_pdf, "iTechPanda CRM | Standard Operating Procedures Manual")

if __name__ == "__main__":
    compile_project_documentation()
    compile_individual_sops()
    compile_combined_sop_manual()
    print("All PDF builds completed successfully!")
