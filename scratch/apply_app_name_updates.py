import os, re

CRM_ROOT = 'CRM_Integrated_v2/CRM'

# 1. Target exact files to update application name
updates = [
    # accounts
    (
        'accounts/context_processors.py',
        [("'APP_NAME': 'TECHPANDA CRM'", "'APP_NAME': 'DigiPanda CRM'")]
    ),
    (
        'accounts/credentials_service.py',
        [("Credentials Service for TECHPANDA CRM.", "Credentials Service for DigiPanda CRM.")]
    ),
    (
        'accounts/breadcrumbs.py',
        [("Centralized Breadcrumb Resolver for TechPanda CRM.", "Centralized Breadcrumb Resolver for DigiPanda CRM.")]
    ),
    (
        'accounts/templatetags/breadcrumb_tags.py',
        [("Django Template Tag Library for TechPanda CRM Dynamic Breadcrumbs.", "Django Template Tag Library for DigiPanda CRM Dynamic Breadcrumbs.")]
    ),
    # chat
    (
        'chat/management/commands/run_campaign_worker.py',
        [("Starting TECHPANDA Bulk WhatsApp Campaign Worker...", "Starting DigiPanda Bulk WhatsApp Campaign Worker...")]
    ),
    (
        'chat/views_campaign.py',
        [("Views for Bulk WhatsApp Campaigns in TECHPANDA CRM.", "Views for Bulk WhatsApp Campaigns in DigiPanda CRM.")]
    ),
    (
        'chat/views.py',
        [
            ("welcome to TECHPANDA!", "welcome to DigiPanda!"),
            ("course inquiry at TECHPANDA.", "course inquiry at DigiPanda."),
            ("programs at TECHPANDA.", "programs at DigiPanda."),
        ]
    ),
    (
        'chat/static/chat/js/flow_builder.js',
        [("Welcome to TECHPANDA WhatsApp.", "Welcome to DigiPanda WhatsApp.")]
    ),
    (
        'chat/templates/chat/inbox.html',
        [
            ("{% block title %}WhatsApp Chats - TECHPANDA CRM{% endblock %}", "{% block title %}WhatsApp Chats - DigiPanda CRM{% endblock %}"),
        ]
    ),
    # fb_leads
    (
        'fb_leads/templates/fb_leads/accounts.html',
        [
            ("{% block title %}Facebook Accounts & Pages - TECHPANDA CRM{% endblock %}", "{% block title %}Facebook Accounts & Pages - DigiPanda CRM{% endblock %}"),
            ('placeholder="e.g. TECHPANDA Digital Marketing / Agency Account"', 'placeholder="e.g. DigiPanda Digital Marketing / Agency Account"'),
        ]
    ),
    (
        'fb_leads/templates/fb_leads/leads.html',
        [
            ("{% block title %}Facebook Leads - TECHPANDA CRM{% endblock %}", "{% block title %}Facebook Leads - DigiPanda CRM{% endblock %}"),
        ]
    ),
    # leads
    (
        'leads/bulk_edit_service.py',
        [("Advanced Bulk Edit & Reassignment Service for TECHPANDA CRM.", "Advanced Bulk Edit & Reassignment Service for DigiPanda CRM.")]
    ),
    (
        'leads/google_sheets_service.py',
        [
            ("authorize TECHPANDA CRM: {url}", "authorize DigiPanda CRM: {url}"),
            ("TECHPANDA CRM: Google Sheets authentication completed", "DigiPanda CRM: Google Sheets authentication completed"),
        ]
    ),
    (
        'leads/management/commands/sync_google_sheet.py',
        [("into TECHPANDA CRM Lead records.", "into DigiPanda CRM Lead records.")]
    ),
    (
        'leads/management/commands/test_smtp_email.py',
        [
            ("=== TECHPANDA CRM SMTP Configuration Diagnostic ===", "=== DigiPanda CRM SMTP Configuration Diagnostic ==="),
            ('subject = "TECHPANDA CRM — SMTP Test Message"', 'subject = "DigiPanda CRM — SMTP Test Message"'),
            ('body = "This is a diagnostic test message sent from TECHPANDA CRM verifying Gmail SMTP delivery."', 'body = "This is a diagnostic test message sent from DigiPanda CRM verifying Gmail SMTP delivery."'),
            ('html = "<p>This is a diagnostic test message sent from <strong>TECHPANDA CRM</strong> verifying Gmail SMTP delivery.</p>"', 'html = "<p>This is a diagnostic test message sent from <strong>DigiPanda CRM</strong> verifying Gmail SMTP delivery.</p>"'),
        ]
    ),
    (
        'leads/views_bulk.py',
        [("API Views for Advanced Bulk Edit Leads in TECHPANDA CRM.", "API Views for Advanced Bulk Edit Leads in DigiPanda CRM.")]
    ),
    (
        'services/__init__.py',
        [("Services package for TECHPANDA CRM.", "Services package for DigiPanda CRM.")]
    ),
]

for rel_path, pairs in updates:
    full_path = os.path.join(CRM_ROOT, rel_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        modified = content
        for target, repl in pairs:
            if target in modified:
                modified = modified.replace(target, repl)
            else:
                print(f"Warning: target not found in {rel_path}: {target[:40]}...")
        if modified != content:
            with open(full_path, 'w', encoding='utf-8', newline='') as f:
                f.write(modified)
            print(f"Updated {rel_path}")

print("Direct file updates completed.")
