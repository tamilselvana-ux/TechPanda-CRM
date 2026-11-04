import re

with open('CRM_Integrated_v2/CRM/templates/public/landing_page.html', 'r', encoding='utf-8') as f:
    text = f.read()

ids = set(re.findall(r'id=["\']([\w-]+)["\']', text))
print("All IDs in landing_page.html:")
for i in sorted(ids):
    print(" -", i)

targets = ['features', 'showcase', 'solutions', 'calculator', 'faq']
print("\nCheck target anchor IDs:")
for t in targets:
    print(f" #{t} exists: {t in ids}")
