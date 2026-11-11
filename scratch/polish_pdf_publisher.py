path = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\scratch\publish_all_pdfs_v2.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Clean CSS @page headers/footers and slightly tighter image max-height so pages flow naturally
old_page_css = """@page {
    size: A4;
    margin: 20mm 15mm 20mm 15mm;
}"""

new_page_css = """@page {
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
}"""

assert old_page_css in content
content = content.replace(old_page_css, new_page_css, 1)

# Tighten figure max-height slightly to prevent half-empty first pages
content = content.replace("max-height: 410px;", "max-height: 310px;", 1)

# Remove Chrome's default URL header/footer by passing --no-pdf-header-footer
old_cmd = '''    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer" if False else "--display-header-footer",
        f"--print-to-pdf={output_pdf}",
        f"--header-template={header_template}",
        f"--footer-template={footer_template}",
        temp_html
    ]'''

new_cmd = '''    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf}",
        temp_html
    ]'''

assert old_cmd in content
content = content.replace(old_cmd, new_cmd, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Polished PDF builder CSS and header/footer flags.")
