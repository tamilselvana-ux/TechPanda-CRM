import os

# 1. Patch leads/views_enrollment.py
path_enr = 'CRM_Integrated_v2/CRM/leads/views_enrollment.py'
with open(path_enr, 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('from .constants import TECHPANDA_INVOICE_CONFIG', 'from .constants import DIGIPANDA_INVOICE_CONFIG, TECHPANDA_INVOICE_CONFIG')
c = c.replace('TECHPANDA_INVOICE_CONFIG', 'DIGIPANDA_INVOICE_CONFIG')
c = c.replace('official TECHPANDA fee receipts', 'official DigiPanda CRM fee receipts')
c = c.replace("'techpanda_crm_secret_key'", "'digipanda_crm_secret_key'")

with open(path_enr, 'w', encoding='utf-8', newline='') as f:
    f.write(c)
print('Updated views_enrollment.py')

# 2. Patch leads/views_accountant.py
path_acc = 'CRM_Integrated_v2/CRM/leads/views_accountant.py'
with open(path_acc, 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('TECHPANDA CRM  FINANCIAL RECONCILIATION REPORT', 'DIGIPANDA CRM — FINANCIAL RECONCILIATION REPORT')
c = c.replace('TechPanda_Financial_Report_', 'DigiPanda_Financial_Report_')

with open(path_acc, 'w', encoding='utf-8', newline='') as f:
    f.write(c)
print('Updated views_accountant.py')

# 3. Patch leads/utils_currency.py, utils_date_filter.py, status_classifier.py
for p in ['CRM_Integrated_v2/CRM/leads/utils_currency.py', 'CRM_Integrated_v2/CRM/leads/utils_date_filter.py', 'CRM_Integrated_v2/CRM/services/status_classifier.py']:
    with open(p, 'r', encoding='utf-8') as f:
        c = f.read()
    c = c.replace('TechPanda CRM', 'DigiPanda CRM')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(c)
    print(f'Updated {p}')

# 4. Patch leads/views.py
path_views = 'CRM_Integrated_v2/CRM/leads/views.py'
with open(path_views, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace("user.set_password('TechPanda@2026')", "user.set_password('DigiPanda@2026')")
with open(path_views, 'w', encoding='utf-8', newline='') as f:
    f.write(c)
print('Updated views.py')

# 5. Patch test assertions
for p in ['CRM_Integrated_v2/CRM/accounts/tests_welcome_email.py', 'CRM_Integrated_v2/CRM/leads/tests_student_emails.py']:
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            c = f.read()
        c = c.replace('Welcome to TECHPANDA CRM', 'Welcome to DigiPanda CRM')
        c = c.replace("COMPANY_NAME='TECHPANDA'", "COMPANY_NAME='DigiPanda CRM'")
        c = c.replace("'company_name': 'TECHPANDA'", "'company_name': 'DigiPanda CRM'")
        with open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(c)
        print(f'Updated {p}')

print('Code level branding updates complete.')
