import os

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\accounts\urls.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    path('api/username-preview/', views.api_username_preview, name='api_username_preview_alt'),"""

replacement = """    path('api/username-preview/', views.api_username_preview, name='api_username_preview_alt'),
    path('toggle-duty-status/', views.toggle_duty_status, name='toggle_duty_status'),"""

assert target in content, "Target not found in accounts/urls.py"
content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated accounts/urls.py with toggle-duty-status")
