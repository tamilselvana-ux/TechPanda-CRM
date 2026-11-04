import os, re

TEMPLATE_DIR = 'CRM_Integrated_v2/CRM/templates'

count = 0
for root, _, filenames in os.walk(TEMPLATE_DIR):
    for f in filenames:
        if f.endswith('.html'):
            fpath = os.path.join(root, f)
            with open(fpath, 'r', encoding='utf-8') as fp:
                content = fp.read()
            
            # Replace variants of title
            new_content = re.sub(r'-\s*DigipandaCRM\b', '- DigiPanda CRM', content)
            new_content = re.sub(r'<title>DigipandaCRM</title>', '<title>DigiPanda CRM</title>', new_content)
            new_content = re.sub(r'-\s*TECHPANDA CRM\b', '- DigiPanda CRM', new_content)
            new_content = re.sub(r'-\s*TechPanda CRM\b', '- DigiPanda CRM', new_content)
            
            if new_content != content:
                with open(fpath, 'w', encoding='utf-8', newline='') as fp:
                    fp.write(new_content)
                count += 1

print(f"Updated {count} HTML templates to 'DigiPanda CRM'.")
