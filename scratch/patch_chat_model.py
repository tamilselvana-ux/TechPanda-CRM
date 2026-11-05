import os

path = 'chat/models.py' if os.path.exists('chat/models.py') else 'CRM/chat/models.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

target = "        return local_time.strftime('%d/%m/%Y')"

prop = """        return local_time.strftime('%d/%m/%Y')

    @property
    def meta_window_info(self):
        \"\"\"
        Calculates Meta 24-hour customer service window.
        Window starts from the customer's last received incoming message.
        \"\"\"
        last_cust_msg = self.messages.filter(sender_type='customer').order_by('-created_at').first()
        if not last_cust_msg:
            return {
                'is_active': False,
                'seconds_remaining': 0,
                'hours_remaining': 0,
                'text': '🟡 24h Window Expired - Template Required',
                'badge_color': '#b45309',
                'bg_color': '#fffbeb',
                'border_color': '#fde68a',
                'requires_template': True
            }
        
        elapsed = (timezone.now() - last_cust_msg.created_at).total_seconds()
        remaining = 86400 - elapsed  # 24 * 3600 = 86400 seconds
        if remaining > 0:
            hrs = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            return {
                'is_active': True,
                'seconds_remaining': int(remaining),
                'hours_remaining': round(remaining / 3600.0, 1),
                'text': f'🟢 24h Window Active: {hrs}h {mins}m left',
                'badge_color': '#047857',
                'bg_color': '#ecfdf5',
                'border_color': '#a7f3d0',
                'requires_template': False
            }
        else:
            return {
                'is_active': False,
                'seconds_remaining': 0,
                'hours_remaining': 0,
                'text': '🟡 24h Window Expired - Template Required',
                'badge_color': '#b45309',
                'bg_color': '#fffbeb',
                'border_color': '#fde68a',
                'requires_template': True
            }"""

if target in code and "meta_window_info" not in code:
    code = code.replace(target, prop, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)
    print("PATCHED_CONVERSATION_META_WINDOW")
else:
    print("TARGET_NOT_FOUND_OR_ALREADY_PATCHED")
