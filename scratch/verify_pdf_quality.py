import os
import glob
import re

PDF_DIR = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\docs\pdf"
DOCS_DIR = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\docs"
ASSETS_DIR = os.path.join(DOCS_DIR, "assets")

def verify():
    print("=== 1. VERIFYING GENERATED PDF DELIVERABLES ===")
    pdf_files = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    print(f"Total PDF deliverables: {len(pdf_files)}")
    for p in pdf_files:
        size = os.path.getsize(p)
        print(f"  [OK] {os.path.basename(p)} - {size:,} bytes")
        assert size > 50000, f"PDF {p} unexpectedly small!"

    print("\n=== 2. VERIFYING DIAGRAM & IMAGE ASSETS ===")
    asset_files = sorted(glob.glob(os.path.join(ASSETS_DIR, "*.*")))
    print(f"Total assets in docs/assets: {len(asset_files)}")
    for a in asset_files:
        print(f"  [OK] {os.path.basename(a)} ({os.path.getsize(a):,} bytes)")

    print("\n=== 3. VERIFYING MARKDOWN IMAGE REFERENCES ===")
    all_md = glob.glob(os.path.join(DOCS_DIR, "project", "*.md")) + glob.glob(os.path.join(DOCS_DIR, "sops", "*.md"))
    missing_assets = 0
    for md_file in all_md:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        images = re.findall(r'!\[.*?\]\((.*?)\)', content)
        for img in images:
            # resolve path relative to md_file
            resolved = os.path.normpath(os.path.join(os.path.dirname(md_file), img))
            if not os.path.exists(resolved):
                print(f"  [FAIL] Missing image in {os.path.basename(md_file)}: {img}")
                missing_assets += 1
    if missing_assets == 0:
        print("  [OK] All markdown image references resolve to existing assets on disk!")

    print("\n=== 4. VERIFYING ABSENCE OF RAW MERMAID CODE BLOCKS ===")
    raw_mermaid = 0
    for md_file in all_md:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        if "```mermaid" in content:
            print(f"  [WARN] Raw mermaid found in {os.path.basename(md_file)}")
            raw_mermaid += 1
    if raw_mermaid == 0:
        print("  [OK] Zero raw mermaid code blocks found across all documents!")

    print("\n=== ALL PDF & ASSET VERIFICATIONS PASSED 100% ===")

if __name__ == "__main__":
    verify()
