import re
import glob

files_found = {}
pattern = re.compile(r'status(?:__in|__iexact)?\s*(?:==|=)\s*([\'\"][A-Za-z0-9 _\-]+[\'\"]|\[[^\]]+\])')

for p in glob.glob(r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\**\*.py', recursive=True):
    if '.venv' in p or 'migrations' in p or 'scratch' in p:
        continue
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    for m in pattern.finditer(text):
        val = m.group(1).strip()
        if any(keyword in val for keyword in ['New', 'Enrolled', 'Interested', 'Lost', 'Demo', 'Discussion', 'RNR', 'Recall', 'Follow-up']):
            files_found.setdefault(val, set()).add(p.split('\\')[-1])

print('=== IDENTIFIED HARDCODED STATUS OCCURRENCES IN BACKEND CODE ===')
for k, v in sorted(files_found.items()):
    print(f'Status Reference: {k} -> referenced in: {sorted(list(v))}')
