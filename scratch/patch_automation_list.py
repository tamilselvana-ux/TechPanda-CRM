import os

file_path = 'CRM_Integrated_v2/CRM/chat/templates/chat/automation_list.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''            <a href="{% url 'login_redirect' %}" class="dash-brand" title="Digipanda CRM" style="display: inline-flex; align-items: center; gap: 8px; text-decoration: none;">
                <img src="{% static 'images/digipanda_symbol.png' %}" alt="Digipanda" width="30" height="30" style="object-fit: contain;">
                <img src="{% static 'images/digipanda_logo.svg' %}" alt="digipanda" class="dash-logo-light" style="height: 24px; width: auto; object-fit: contain;">
                <img src="{% static 'images/digipanda_logo_dark.svg' %}" alt="digipanda" class="dash-logo-dark" style="height: 24px; width: auto; object-fit: contain;">
                <span class="dash-badge-automations">AUTOMATIONS</span>
            </a>'''

replacement = '''            <a href="{% url 'login_redirect' %}" class="dash-brand" title="DigiPanda CRM" style="display: inline-flex; align-items: center; gap: 8px; text-decoration: none;">
                <img src="{% static 'images/digipanda_symbol.png' %}" alt="DigiPanda CRM" width="30" height="30" style="object-fit: contain;">
                <span style="font-weight: 800; font-size: 1.05rem; letter-spacing: -0.02em; font-family: 'Plus Jakarta Sans', sans-serif;">
                    <span style="color: #0a53b5;">digi</span><span style="color: #2bb34b;">p</span><span style="color: var(--tp-text-primary, #0f172a);">anda</span>
                </span>
                <span class="dash-badge-automations">AUTOMATIONS</span>
            </a>'''

norm_content = content.replace('\r\n', '\n')
norm_target = target.replace('\r\n', '\n')
norm_replacement = replacement.replace('\r\n', '\n')

if norm_target in norm_content:
    norm_content = norm_content.replace(norm_target, norm_replacement)
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(norm_content)
    print("Updated automation_list.html successfully.")
else:
    print("Target not found in automation_list.html.")
