import os
import sys

base_dir = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM"
sys.path.insert(0, base_dir)

# Read views and check how they extract date filters
files_to_check = [
    os.path.join(base_dir, "leads", "views.py"),
    os.path.join(base_dir, "accounts", "views.py"),
    os.path.join(base_dir, "calls", "views.py"),
    os.path.join(base_dir, "finance", "views.py"),
    os.path.join(base_dir, "leads", "utils_date_filter.py"),
]

for fp in files_to_check:
    print("=" * 60)
    print(fp)
    if not os.path.exists(fp):
        print("Does not exist!")
        continue
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    # Print occurrences of request.GET.get for dates
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if any(w in line for w in ["extract_normalized_date_range", "date_from", "from_date", "start_date", "period"]):
            if "def " in line or "request.GET" in line or "extract_normalized_date_range" in line or "filter(" in line:
                print(f"L{i+1}: {line.strip()}")
