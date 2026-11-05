import os

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\accounts\views.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = "from django.http import JsonResponse"
replacement = "from django.http import JsonResponse\nfrom django.views.decorators.http import require_POST"

assert target in content, "Target not found in accounts/views.py"
content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Imported require_POST in accounts/views.py")
