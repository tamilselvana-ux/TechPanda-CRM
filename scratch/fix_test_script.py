import os

path = 'CRM/scratch/test_whatsapp_window_kit.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("sender_type=Message.SENDER_CUSTOMER", "sender=Message.SENDER_CUSTOMER")
text = text.replace("last_msg.sender_type", "last_msg.sender")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("UPDATED_TEST_SCRIPT")
