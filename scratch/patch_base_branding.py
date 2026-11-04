import os, re

BASE_HTML = 'CRM_Integrated_v2/CRM/templates/base.html'

with open(BASE_HTML, 'r', encoding='utf-8') as f:
    base_content = f.read()

# 1. Update <title> block in base.html
base_content = re.sub(
    r'<title>\{% block title %\}DigipandaCRM\{% endblock %\}</title>',
    '<title>{% block title %}DigiPanda CRM{% endblock %}</title>',
    base_content
)

# 2. Update sidebar header in base.html
sidebar_header_old = '''      <div class="sidebar-header">
        <a href="{% url 'login_redirect' %}" class="brand-logo" style="display: flex; align-items: center; gap: 8px; text-decoration: none;">
          <img src="{% static 'images/digipanda_symbol.png' %}" alt="DigiPanda" width="30" height="30" style="object-fit: contain; flex-shrink: 0;" class="brand-symbol">
          <div class="brand-text" style="display: flex; align-items: center; gap: 6px;">
            <img src="{% static 'images/digipanda_logo.svg' %}" alt="DigiPanda" class="brand-logo-light" style="height: 24px; width: auto; max-width: 130px; object-fit: contain;">
            <img src="{% static 'images/digipanda_logo_dark.svg' %}" alt="DigiPanda" class="brand-logo-dark" style="height: 24px; width: auto; max-width: 130px; object-fit: contain;">
            <span class="part-crm" style="color: #2bb34b; font-weight: 800; font-size: 0.72rem; letter-spacing: 0.04em; background: rgba(43, 179, 75, 0.12); border: 1px solid rgba(43, 179, 75, 0.3); padding: 1px 5px; border-radius: 5px;">CRM</span>
          </div>
        </a>
      </div>'''

sidebar_header_new = '''      <div class="sidebar-header">
        <a href="{% url 'login_redirect' %}" class="brand-logo" style="display: flex; align-items: center; gap: 9px; text-decoration: none;">
          <img src="{% static 'images/digipanda_symbol.png' %}" alt="DigiPanda CRM" width="32" height="32" style="object-fit: contain; flex-shrink: 0;" class="brand-symbol">
          <div class="brand-text" style="display: flex; align-items: center; gap: 6px; overflow: hidden; white-space: nowrap;">
            <span class="brand-name" style="font-size: 1.15rem; font-weight: 800; letter-spacing: -0.02em; font-family: 'Plus Jakarta Sans', var(--font-primary, sans-serif);">
              <span style="color: #0a53b5;">digi</span><span style="color: #2bb34b;">p</span><span style="color: var(--tp-text-primary, #0f172a);">anda</span>
            </span>
            <span class="part-crm" style="color: #0a53b5; font-weight: 800; font-size: 0.74rem; letter-spacing: 0.04em; background: rgba(10, 83, 181, 0.1); border: 1px solid rgba(10, 83, 181, 0.28); padding: 1px 6px; border-radius: 5px;">CRM</span>
          </div>
        </a>
      </div>'''

# Handle CRLF / LF variations
if sidebar_header_old in base_content:
    base_content = base_content.replace(sidebar_header_old, sidebar_header_new)
    print("Replaced sidebar-header cleanly.")
else:
    # Try normalizing newlines
    base_norm = base_content.replace('\r\n', '\n')
    if sidebar_header_old.replace('\r\n', '\n') in base_norm:
        base_norm = base_norm.replace(sidebar_header_old.replace('\r\n', '\n'), sidebar_header_new.replace('\r\n', '\n'))
        base_content = base_norm
        print("Replaced sidebar-header with normalized newlines.")
    else:
        print("Warning: sidebar_header_old pattern not matched exactly.")

# 3. Update top app-header in base.html
header_brand_old = '''          <a href="{% url 'login_redirect' %}" class="header-brand-link" style="display: flex; align-items: center; gap: 6px; text-decoration: none;">
            <img src="{% static 'images/digipanda_logo.svg' %}" alt="DigiPanda" class="brand-logo-light" style="height: 25px; width: auto; max-width: 140px; object-fit: contain;">
            <img src="{% static 'images/digipanda_logo_dark.svg' %}" alt="DigiPanda" class="brand-logo-dark" style="height: 25px; width: auto; max-width: 140px; object-fit: contain;">
            <span class="part-crm" style="color: #2bb34b; font-weight: 800; font-size: 0.72rem; letter-spacing: 0.04em; background: rgba(43, 179, 75, 0.12); border: 1px solid rgba(43, 179, 75, 0.3); padding: 1px 5px; border-radius: 5px;">CRM</span>
          </a>'''

header_brand_new = '''          <a href="{% url 'login_redirect' %}" class="header-brand-link" style="display: flex; align-items: center; gap: 8px; text-decoration: none;">
            <img src="{% static 'images/digipanda_symbol.png' %}" alt="DigiPanda CRM" width="28" height="28" style="object-fit: contain; flex-shrink: 0;" class="brand-symbol">
            <span class="brand-name" style="font-size: 1.05rem; font-weight: 800; letter-spacing: -0.02em; font-family: 'Plus Jakarta Sans', var(--font-primary, sans-serif);">
              <span style="color: #0a53b5;">digi</span><span style="color: #2bb34b;">p</span><span style="color: var(--tp-text-primary, #0f172a);">anda</span>
            </span>
            <span class="part-crm" style="color: #0a53b5; font-weight: 800; font-size: 0.7rem; letter-spacing: 0.04em; background: rgba(10, 83, 181, 0.1); border: 1px solid rgba(10, 83, 181, 0.28); padding: 1px 5px; border-radius: 5px;">CRM</span>
          </a>'''

base_norm = base_content.replace('\r\n', '\n')
if header_brand_old.replace('\r\n', '\n') in base_norm:
    base_norm = base_norm.replace(header_brand_old.replace('\r\n', '\n'), header_brand_new.replace('\r\n', '\n'))
    base_content = base_norm
    print("Replaced header-brand-link cleanly.")
else:
    print("Warning: header_brand_old pattern not matched.")

with open(BASE_HTML, 'w', encoding='utf-8', newline='') as f:
    f.write(base_content)

print("Updated base.html successfully.")
