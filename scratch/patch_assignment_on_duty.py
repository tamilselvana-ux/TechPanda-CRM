import os

# 1. Patch assignment.py
path_assign = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\assignment.py'
with open(path_assign, 'r', encoding='utf-8') as f:
    c_assign = f.read()

c_assign = c_assign.replace("telecaller__is_active=True,\n            telecaller__role=UserRole.TELECALLER", "telecaller__is_active=True,\n            telecaller__is_on_duty=True,\n            telecaller__role=UserRole.TELECALLER")
c_assign = c_assign.replace("telecaller__is_active=True\n        ).exclude(telecaller=old_tc)", "telecaller__is_active=True,\n            telecaller__is_on_duty=True\n        ).exclude(telecaller=old_tc)")

with open(path_assign, 'w', encoding='utf-8') as f:
    f.write(c_assign)
print("Updated leads/assignment.py with telecaller__is_on_duty check")

# 2. Patch allocation_service.py
path_alloc = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\allocation_service.py'
with open(path_alloc, 'r', encoding='utf-8') as f:
    c_alloc = f.read()

c_alloc = c_alloc.replace("telecaller__is_active=True\n    ).select_related('telecaller', 'channel')", "telecaller__is_active=True,\n        telecaller__is_on_duty=True\n    ).select_related('telecaller', 'channel')")
c_alloc = c_alloc.replace("telecaller__is_active=True\n    ).select_related('telecaller')", "telecaller__is_active=True,\n        telecaller__is_on_duty=True\n    ).select_related('telecaller')")

with open(path_alloc, 'w', encoding='utf-8') as f:
    f.write(c_alloc)
print("Updated leads/allocation_service.py with telecaller__is_on_duty check")
