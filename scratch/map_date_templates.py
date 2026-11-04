import os, re, sys

sys.path.insert(0, os.path.abspath('CRM_Integrated_v2/CRM'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.urls import get_resolver

CRM_ROOT = 'CRM_Integrated_v2/CRM'

# 1. Identify all templates having date filters
date_filter_pages = []

template_dir = os.path.join(CRM_ROOT, 'templates')

for root, _, files in os.walk(template_dir):
    for f in files:
        if not f.endswith('.html'):
            continue
        fpath = os.path.join(root, f)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
            txt = fp.read()
        
        # Check if template has date filter inputs or forms
        # Ignore forms for creating/editing dates (e.g. dob, follow-up schedule datetime)
        has_filter_form = bool(re.search(r'<form[^>]*method=[\'"]GET[\'"][^>]*>.*?(?:date_from|date_to|start_date|end_date|name=[\'"]from[\'"]|name=[\'"]to[\'"]|name=[\'"]period[\'"]).*?</form>', txt, re.DOTALL | re.IGNORECASE))
        has_smart_cal = 'smart-calendar' in txt or 'data-smart-calendar' in txt or 'tp-date-range-badge' in txt
        
        if has_filter_form or has_smart_cal:
            rel = os.path.relpath(fpath, CRM_ROOT).replace('\\', '/')
            # find input names
            names = re.findall(r'name=[\'"](date_from|date_to|start_date|end_date|from|to|period)[\'"]', txt, re.IGNORECASE)
            date_filter_pages.append((rel, list(set(names))))

print(f"Found {len(date_filter_pages)} templates with GET date filter forms / smart calendar triggers:")
for t, n in sorted(date_filter_pages):
    print(f"  - {t} (inputs: {n})")
