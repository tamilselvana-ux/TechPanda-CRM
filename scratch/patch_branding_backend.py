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
    else:
        print(f"No changes in {path}")

# 1. settings.py
replace_in_file('CRM/config/settings.py', [
    ('DigiPanda Academy', 'iTechPanda CRM'),
    ('DigiPanda CRM', 'iTechPanda CRM'),
    ('DIGIPANDA CRM', 'iTechPanda CRM'),
    ('admin@digipandaacademy.com', 'admin@itechpanda.com'),
    ('https://digipandacrm.in', 'https://itechpanda.com'),
    ('https://www.digipandacrm.in', 'https://www.itechpanda.com'),
])

# 2. context_processors.py
replace_in_file('CRM/accounts/context_processors.py', [
    ("'APP_NAME': 'DigiPanda CRM'", "'APP_NAME': 'iTechPanda CRM', 'COMPANY_NAME': 'iTechPanda CRM'"),
    ("'APP_NAME': 'TechPanda CRM'", "'APP_NAME': 'iTechPanda CRM', 'COMPANY_NAME': 'iTechPanda CRM'"),
])

# 3. email_service.py
replace_in_file('CRM/services/email_service.py', [
    ('digipanda_logo.png', 'itechpanda_logo.png'),
    ('digipanda_email_logo.png', 'itechpanda_logo.png'),
    ('digipanda_logo', 'itechpanda_logo'),
    ('DigiPanda CRM', 'iTechPanda CRM'),
    ('DIGIPANDA', 'iTechPanda CRM'),
    ('DigiPanda Academy', 'iTechPanda CRM'),
    ('DigiPanda_Receipt_', 'iTechPanda_Receipt_'),
    ('https://learn.digipanda.in', 'https://learn.itechpanda.com'),
    ('https://pay.digipanda.in', 'https://pay.itechpanda.com'),
    ('support@digipanda.in', 'support@itechpanda.com'),
])

# 4. accounts/services.py
replace_in_file('CRM/accounts/services.py', [
    ('DigiPanda CRM', 'iTechPanda CRM'),
    ('DIGIPANDA', 'iTechPanda CRM'),
    ('no-reply@digipanda.academy', 'no-reply@itechpanda.com'),
])

print("Backend branding patched successfully!")
