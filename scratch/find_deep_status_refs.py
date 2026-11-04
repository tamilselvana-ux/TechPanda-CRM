import re
import glob

key_statuses = ['New', 'Enrolled', 'Demo Scheduled', 'Interested', 'Lost', 'Discussion', 'Follow-up', 'Converted', 'Admission Taken']

found = {}
for p in glob.glob(r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\**\*.py', recursive=True):
    if '.venv' in p or 'migrations' in p or 'scratch' in p or 'test' in p:
        continue
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for idx, line in enumerate(lines, 1):
        for s in key_statuses:
            if f"'{s}'" in line or f'"{s}"' in line:
                if 'status' in line.lower() or 'lead' in line.lower():
                    found.setdefault(s, []).append((p.split('\\')[-1], idx, line.strip()))

for s, refs in sorted(found.items()):
    print(f"\n--- Status: '{s}' ({len(refs)} references) ---")
    for fname, lno, snippet in refs[:6]:
        print(f"  [{fname}:{lno}] {snippet[:90]}")
