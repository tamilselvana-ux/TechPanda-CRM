import os

path = 'chat/views.py' if os.path.exists('chat/views.py') else 'CRM/chat/views.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("sender_type=Message.SENDER_AGENT", "sender=Message.SENDER_AGENT")
text = text.replace("sent_at=timezone.now()", "timestamp=timezone.now()")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("UPDATED_CHAT_VIEWS_SENDER_FIELD")
