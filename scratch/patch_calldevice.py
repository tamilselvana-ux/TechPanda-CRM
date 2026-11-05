import os

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\models.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    last_recording_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s phone\""""

replacement = """    last_recording_at = models.DateTimeField(null=True, blank=True)
    battery_percent = models.IntegerField(null=True, blank=True, help_text="Device battery percentage (0-100)")
    is_charging = models.BooleanField(default=False, help_text="True if device is plugged into power")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s phone"

    @property
    def is_online(self):
        if not self.last_seen_at:
            return False
        return (timezone.now() - self.last_seen_at).total_seconds() <= 120"""

assert target in content, "Target not found in calls/models.py"
content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated CallDevice in calls/models.py")
