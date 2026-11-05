import os

path = 'leads/views.py' if os.path.exists('leads/views.py') else 'CRM/leads/views.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = "'assigned_counselor': (m.assigned_counselor.get_full_name() or m.assigned_counselor.username) if m.assigned_counselor else None,"
replacement = target + """\n            'assigned_counselor_id': m.assigned_counselor_id if m.assigned_counselor_id else None,\n            'course_id': getattr(m, 'product_id', None),\n            'course_name': m.product.name if getattr(m, 'product', None) else (getattr(m, 'course_name', '') or ''),\n            'category': getattr(m, 'category', '') or 'Training',"""

if target in content:
    content = content.replace(target, replacement, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("PATCH_SUCCESS")
else:
    print("TARGET_NOT_FOUND")
