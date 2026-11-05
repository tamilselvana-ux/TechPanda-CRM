import os

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\accounts\models.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    invitation_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Setup'),
            ('SENT', 'Invitation Sent'),
            ('FAILED', 'Delivery Failed'),
            ('ACTIVATED', 'Activated'),
        ],
        default='PENDING',
        help_text="Onboarding invitation status"
    )"""

replacement = """    invitation_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Setup'),
            ('SENT', 'Invitation Sent'),
            ('FAILED', 'Delivery Failed'),
            ('ACTIVATED', 'Activated'),
        ],
        default='PENDING',
        help_text="Onboarding invitation status"
    )
    is_on_duty = models.BooleanField(
        default=True,
        help_text="True if staff is actively on duty and available for automated lead assignment"
    )"""

assert target in content, "Target not found in accounts/models.py"
content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated User model in accounts/models.py")
