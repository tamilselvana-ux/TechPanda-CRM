import os

def replace_in_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    for old, new in replacements:
        content = content.replace(old, new)
    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {path}")

# 1. walkin_form_editor.html & walkin_form_qr_poster.html
replace_in_file('CRM/templates/admin/walkin_form_editor.html', [
    ("placeholder=\"digipanda\"", "placeholder=\"iTechPanda\""),
    ("default:'digipanda'", "default:'iTechPanda'"),
    ("|| 'digipanda'", "|| 'iTechPanda'"),
])

replace_in_file('CRM/templates/admin/walkin_form_qr_poster.html', [
    ('default:"digipanda"', 'default:"iTechPanda"'),
])

# 2. emails
email_replacements = [
    ('https://www.digipanda.com', 'https://www.itechpanda.com'),
    ('https://www.digipandaacademy.com', 'https://www.itechpanda.com'),
    ('cid:digipanda_logo', 'cid:itechpanda_logo'),
    ('alt="digipanda"', 'alt="iTechPanda"'),
    ('admin@digipanda.com', 'admin@itechpanda.com'),
    ('admin@digipandaacademy.com', 'admin@itechpanda.com'),
    ('www.digipanda.com', 'www.itechpanda.com'),
    ('facebook.com/digipanda', 'facebook.com/itechpanda'),
    ('instagram.com/digipanda', 'instagram.com/itechpanda'),
    ('linkedin.com/company/digipanda', 'linkedin.com/company/itechpanda'),
    ('youtube.com/digipanda', 'youtube.com/itechpanda'),
    ('<span style="color: #003a93;">digi</span>', '<span style="color: #174b89;">itech</span>'),
    ('<span style="color: #1ea12c;">p</span>', '<span style="color: #36b44c;">p</span>'),
    ('<span style="color: #1c1a19;">anda</span>', '<span style="color: #262221;">anda</span>'),
]

for em in ['enrollment_confirmation.html', 'installment_reminder.html', 'payment_receipt.html']:
    replace_in_file(os.path.join('CRM/templates/emails', em), email_replacements)

print("Final 5 templates patched cleanly!")
