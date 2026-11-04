import os

STATIC_DIR = 'CRM/static'

REPLACEMENTS = [
    ('DigiPanda Academy', 'iTechPanda Academy'),
    ('Digipanda Academy', 'iTechPanda Academy'),
    ('DigiPanda CRM', 'iTechPanda CRM'),
    ('Digipanda CRM', 'iTechPanda CRM'),
    ('DIGIPANDA CRM', 'iTechPanda CRM'),
    ('DigiPanda', 'iTechPanda'),
    ('Digipanda', 'iTechPanda'),
    ('DIGIPANDA', 'iTechPanda'),
    ('digipanda_logo.png', 'itechpanda_logo.png'),
    ('digipanda_symbol.png', 'itechpanda_symbol.png'),
]

files_changed = 0
for root, _, files in os.walk(STATIC_DIR):
    for f in files:
        if f.endswith('.js') or f.endswith('.css'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fh:
                content = fh.read()
            orig = content
            for old, new in REPLACEMENTS:
                content = content.replace(old, new)
            if content != orig:
                with open(p, 'w', encoding='utf-8') as fh:
                    fh.write(content)
                files_changed += 1
                print(f"Patched static: {p}")

print(f"\nStatic patching complete: {files_changed} files updated.")
