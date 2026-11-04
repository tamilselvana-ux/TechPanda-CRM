import os, re

template_dir = 'CRM_Integrated_v2/CRM/templates'
date_templates = []

for r, _, fnames in os.walk(template_dir):
    for f in fnames:
        if f.endswith('.html'):
            path = os.path.join(r, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                txt = fp.read()
            # Look for type='date', name='date_from', name='from', name='start_date', smart-calendar, date-range, etc.
            matches = re.findall(r'(type=[\'"]date[\'"]|name=[\'"](?:date_from|date_to|start_date|end_date|from|to|period)[\'"]|class=[\'"][^\'"]*(?:date-picker|smart-calendar|date-range)[^\'"]*[\'"])', txt, re.IGNORECASE)
            if matches:
                date_templates.append((path.replace('\\', '/'), matches))

for p, m in sorted(date_templates, key=lambda x: x[0]):
    print(f'{p}: {len(m)} elements -> {m[:5]}')
