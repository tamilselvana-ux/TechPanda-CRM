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

# Core python files
replace_in_file('CRM/accounts/backends.py', [('DigiPanda CRM', 'iTechPanda CRM')])
replace_in_file('CRM/accounts/breadcrumbs.py', [('DigiPanda CRM', 'iTechPanda CRM')])
replace_in_file('CRM/accounts/credentials_service.py', [('DigiPanda CRM', 'iTechPanda CRM')])
replace_in_file('CRM/accounts/views.py', [('DigiPanda CRM Login', 'iTechPanda CRM Login'), ('DigiPanda CRM', 'iTechPanda CRM')])
replace_in_file('CRM/accounts/views_public.py', [('Digipanda CRM', 'iTechPanda CRM'), ('https://digipandacrm.in/', 'https://itechpanda.com/'), ('https://digipandacrm.in', 'https://itechpanda.com')])
replace_in_file('CRM/config/sitemaps.py', [('Digipanda CRM', 'iTechPanda CRM'), ('digipandacrm.in', 'itechpanda.com')])
replace_in_file('CRM/chat/campaign_service.py', [
    ('DigiPanda CRM', 'iTechPanda CRM'),
    ('DIGIPANDA Official Admissions Line', 'iTechPanda Official Admissions Line'),
    ('DIGIPANDA Academy', 'iTechPanda Academy'),
    ('DIGIPANDA Learning', 'iTechPanda Learning'),
    ('DIGIPANDA Admissions', 'iTechPanda Admissions'),
    ('DIGIPANDA', 'iTechPanda'),
    ('DigiPanda', 'iTechPanda'),
])
replace_in_file('CRM/chat/views.py', [
    ('at DigiPanda', 'at iTechPanda'),
    ('to DigiPanda', 'to iTechPanda'),
    ('DigiPanda CRM', 'iTechPanda CRM'),
])
replace_in_file('CRM/leads/bulk_edit_service.py', [('DigiPanda CRM', 'iTechPanda CRM')])
replace_in_file('CRM/leads/google_sheets_service.py', [('DigiPanda CRM', 'iTechPanda CRM')])
replace_in_file('CRM/leads/kpi_registry.py', [('DigiPanda CRM', 'iTechPanda CRM')])
replace_in_file('CRM/leads/views_accountant.py', [
    ('DIGIPANDA CRM - FINANCIAL RECONCILIATION REPORT', 'ITECHPANDA CRM - FINANCIAL RECONCILIATION REPORT'),
    ('DigiPanda_Financial_Report_', 'iTechPanda_Financial_Report_'),
])
replace_in_file('CRM/leads/views_walkin.py', [
    ("branding['brand_name'] = 'digipanda'", "branding['brand_name'] = 'itechpanda'"),
])
replace_in_file('CRM/leads/views.py', [
    ("'DigiPanda@2026'", "'iTechPanda@2026'"),
    ("DigiPanda CRM", "iTechPanda CRM"),
])
replace_in_file('CRM/services/status_classifier.py', [('DigiPanda CRM', 'iTechPanda CRM')])

print("Core python files updated to iTechPanda successfully!")
