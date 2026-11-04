import os

files = [
    'CRM_Integrated_v2/CRM/templates/emails/enrollment_confirmation.html',
    'CRM_Integrated_v2/CRM/templates/emails/installment_reminder.html',
    'CRM_Integrated_v2/CRM/templates/emails/payment_receipt.html',
]

target = '''<a href="https://www.digipandaacademy.com" target="_blank" style="text-decoration: none; display: inline-block;">
                        <div style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 32px; font-weight: 900; letter-spacing: -0.5px; line-height: 1;">
                          <span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span>
                        </div>
                      </a>'''

replacement = '''<a href="https://www.digipandaacademy.com" target="_blank" style="text-decoration: none; display: inline-block;">
                        <img src="cid:digipanda_logo" alt="digipanda" width="160" height="56" style="display: block; width: 160px; max-width: 160px; height: auto; max-height: 56px; border: 0; outline: none; text-decoration: none;" />
                      </a>'''

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    if target in content:
        content = content.replace(target, replacement)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Updated:', fpath)
    else:
        print('Target not matched in:', fpath)
