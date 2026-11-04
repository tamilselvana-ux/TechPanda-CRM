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

replace_in_file('CRM/leads/constants.py', [
    ("'company_name': 'DigiPanda'", "'company_name': 'iTechPanda'"),
    ("'company_legal_name': 'DigiPanda Software Training Private Limited'", "'company_legal_name': 'iTechPanda Software Training Private Limited'"),
    ("'email': 'admin@digipandaacademy.com'", "'email': 'admin@itechpanda.com'"),
    ("'website': 'www.digipandaacademy.com'", "'website': 'www.itechpanda.com'"),
    ("'name': 'DigiPanda Software Training Private Limited'", "'name': 'iTechPanda Software Training Private Limited'"),
    ("'signatory_label': 'AUTHORISED SIGNATORY FOR DigiPanda'", "'signatory_label': 'AUTHORISED SIGNATORY FOR iTechPanda'"),
])

replace_in_file('CRM/leads/views_enrollment.py', [
    ('DigiPanda CRM', 'iTechPanda CRM'),
    ('DigiPanda Towers', 'iTechPanda Towers'),
    ('DigiPanda_Receipt_', 'iTechPanda_Receipt_'),
    ("'digipanda_logo.png'", "'itechpanda_logo.png'"),
])

print("Constants and views_enrollment updated successfully!")
