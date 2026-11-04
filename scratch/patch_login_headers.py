import os, re

login_files = [
    'CRM_Integrated_v2/CRM/templates/registration/login.html',
    'CRM_Integrated_v2/CRM/templates/registration/admin_login.html',
    'CRM_Integrated_v2/CRM/templates/registration/manager_login.html',
    'CRM_Integrated_v2/CRM/templates/registration/telecaller_login.html',
    'CRM_Integrated_v2/CRM/templates/finance/login.html',
]

new_block = '''      <div style="margin-bottom: 18px; display: flex; flex-direction: column; align-items: center; gap: 8px;">
        <img src="{% static 'images/digipanda_symbol.png' %}" alt="DigiPanda CRM" style="height: 52px; width: 52px; object-fit: contain;">
        <div style="font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em; font-family: 'Plus Jakarta Sans', var(--font-primary, sans-serif);">
          <span style="color: #0a53b5;">digi</span><span style="color: #2bb34b;">p</span><span style="color: var(--tp-text-primary, #0f172a);">anda</span><span style="color: #0a53b5; font-size: 0.85rem; margin-left: 3px; font-weight: 800; text-transform: uppercase;">crm</span>
        </div>
      </div>'''

for lf in login_files:
    if os.path.exists(lf):
        with open(lf, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Regex to find <div style="margin-bottom: 16px;...">...<img ...digipanda_logo...</div>
        pattern = r'<div style="margin-bottom:\s*16px;[^"]*">\s*<img src="{% static \'images/digipanda_logo\.png\' %}"[^>]*>\s*<img src="{% static \'images/digipanda_logo_dark\.png\' %}"[^>]*>\s*</div>'
        
        if re.search(pattern, content):
            content = re.sub(pattern, new_block, content)
            with open(lf, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            print(f"Updated login header in {lf}")
        else:
            print(f"Pattern not found in {lf}")

print("Login template patch completed.")
