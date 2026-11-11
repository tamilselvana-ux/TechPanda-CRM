import os, re, glob

DOCS_DIR = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\docs"
PDF_DIR = os.path.join(DOCS_DIR, "pdf")
SOPS_DIR = os.path.join(DOCS_DIR, "sops")

# 1. Verify every image link in Markdown resolves on disk and no raw mermaid blocks exist
md_files = [os.path.join(DOCS_DIR, "01_Project_Document.md")] + sorted(glob.glob(os.path.join(SOPS_DIR, "*.md")))
missing_imgs = []
raw_mermaid = []
total_imgs = 0

for fpath in md_files:
    base = os.path.dirname(fpath)
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()
    if "```mermaid" in text:
        raw_mermaid.append(fpath)
    for m in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', text):
        total_imgs += 1
        rel = m.group(2)
        abs_p = os.path.normpath(os.path.join(base, rel))
        if not os.path.exists(abs_p) or os.path.getsize(abs_p) < 1000:
            missing_imgs.append((os.path.basename(fpath), rel))

print(f"Markdown files checked: {len(md_files)}")
print(f"Total embedded image references verified: {total_imgs}")
print(f"Missing or empty images: {missing_imgs}")
print(f"Raw mermaid blocks left: {raw_mermaid}")

# 2. Verify all 27 new PDFs exist and have valid PDF header
expected_pdfs = ["01_Project_Document.pdf", "00_SOP_Index.pdf", "SOP_Manual_All_Roles_Complete.pdf"] + [
    os.path.basename(p).replace(".md", ".pdf") for p in sorted(glob.glob(os.path.join(SOPS_DIR, "SOP-*.md")))
]
for pdf in expected_pdfs:
    p = os.path.join(PDF_DIR, pdf)
    assert os.path.exists(p), f"Missing PDF: {pdf}"
    with open(p, "rb") as f:
        hdr = f.read(5)
    assert hdr == b"%PDF-", f"Invalid PDF header in {pdf}: {hdr}"
    assert os.path.getsize(p) > 50_000, f"PDF unusually small: {pdf}"

print(f"All {len(expected_pdfs)} PDFs verified valid (%PDF- header & >50 KB each)!")
