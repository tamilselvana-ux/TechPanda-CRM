import os
import re

TEMPLATES_DIR = 'CRM/templates'

REPLACEMENTS = [
    # Image references
    ('digipanda_symbol.png', 'itechpanda_symbol.png'),
    ('digipanda_symbol.svg', 'itechpanda_symbol.svg'),
    ('digipanda_logo.png', 'itechpanda_logo.png'),
    ('digipanda_logo.svg', 'itechpanda_logo.svg'),
    ('digipanda_crm_logo.png', 'itechpanda_logo.png'),
    ('digipanda_logo_hd.png', 'itechpanda_logo.png'),
    ('digipanda_official_logo.png', 'itechpanda_logo.png'),
    ('digipanda_email_logo.png', 'itechpanda_logo.png'),
    ('digipanda_logo_dark.png', 'itechpanda_logo_white.png'),
    ('digipanda_logo_dark.svg', 'itechpanda_logo_white.svg'),
    ('digipanda_exact_darkmode@2x.png', 'itechpanda_logo_white.png'),
    
    # Text Wordmarks with span tags
    ('<span style="color: #0a53b5;">digi</span>', '<span style="color: #174b89;">itech</span>'),
    ('<span style="color: #0a53b5;">Digi</span>', '<span style="color: #174b89;">iTech</span>'),
    ('<span style="color: #2bb34b;">p</span>', '<span style="color: #36b44c;">p</span>'),
    ('<span style="color: var(--tp-text-primary, #0f172a);">anda</span>', '<span style="color: var(--tp-text-primary, #262221);">anda</span>'),
    ('<span class="part-digi">Digi</span>', '<span class="part-itech">iTech</span>'),
    ('<span class="part-digi">digi</span>', '<span class="part-itech">itech</span>'),
    ('<span class="part-digi">DIGI</span>', '<span class="part-itech">ITECH</span>'),
    ('class="part-digi"', 'class="part-itech"'),

    # Brand titles and names
    ('DigiPanda Academy', 'iTechPanda Academy'),
    ('Digipanda Academy', 'iTechPanda Academy'),
    ('DIGIPANDA ACADEMY', 'ITECHPANDA ACADEMY'),
    ('DigiPanda CRM', 'iTechPanda CRM'),
    ('Digipanda CRM', 'iTechPanda CRM'),
    ('DIGIPANDA CRM', 'iTechPanda CRM'),
    ('DigiPanda', 'iTechPanda'),
    ('Digipanda', 'iTechPanda'),
    ('DIGIPANDA', 'iTechPanda'),
    ('digipandacrm.in', 'itechpanda.com'),
    ('digipanda.in', 'itechpanda.com'),
    ('digipanda.academy', 'itechpanda.com'),
    ('digipandacrm', 'itechpandacrm'),
]

files_changed = 0
total_replacements = 0

for root, _, files in os.walk(TEMPLATES_DIR):
    for f in files:
        if f.endswith('.html') or f.endswith('.txt'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fh:
                content = fh.read()
            orig = content
            rep_count = 0
            for old, new in REPLACEMENTS:
                if old in content:
                    count = content.count(old)
                    content = content.replace(old, new)
                    rep_count += count
            if content != orig:
                with open(p, 'w', encoding='utf-8') as fh:
                    fh.write(content)
                files_changed += 1
                total_replacements += rep_count
                print(f"Patched: {p} ({rep_count} replacements)")

print(f"\nDONE: {files_changed} templates updated, {total_replacements} replacements made.")
