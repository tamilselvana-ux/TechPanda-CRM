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

replace_in_file('CRM/accounts/tests_welcome_email.py', [
    ("Welcome to DigiPanda CRM", "Welcome to iTechPanda CRM"),
    ("Welcome to TechPanda CRM", "Welcome to iTechPanda CRM"),
    ("Welcome to TECHPANDA CRM", "Welcome to iTechPanda CRM"),
])

replace_in_file('CRM/leads/tests_student_emails.py', [
    ("COMPANY_NAME='DigiPanda CRM'", "COMPANY_NAME='iTechPanda CRM'"),
    ("'company_name': 'DigiPanda CRM'", "'company_name': 'iTechPanda CRM'"),
    ("'company_name': 'DIGIPANDA'", "'company_name': 'iTechPanda CRM'"),
])

replace_in_file('CRM/leads/tests_landing_page_integrity.py', [
    ("'DigiPanda'", "'iTechPanda'"),
    ("'Digipanda'", "'iTechPanda'"),
])

replace_in_file('CRM/leads/tests_dom_structural_integrity.py', [
    ("Leads - DigipandaCRM", "Leads - iTechPanda CRM"),
    ("DigipandaCRM", "iTechPanda CRM"),
])

replace_in_file('CRM/leads/tests_frontend_integrity.py', [
    ("Leads - DigipandaCRM", "Leads - iTechPanda CRM"),
    ("DigipandaCRM", "iTechPanda CRM"),
])

print("Test assertions updated to iTechPanda!")
