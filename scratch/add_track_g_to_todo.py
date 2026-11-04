todo_path = r'D:\CRM_Integrated_v2\TODO.md'
with open(todo_path, 'r', encoding='utf-8') as f:
    text = f.read()

track_g = """
---

## Track G: Hostinger Mailbox Integration (admin@digipandaacademy.com)

- [ ] **Item 62 — Django Settings & Dynamic SSL/TLS Support**: Update `config/settings.py` so `EMAIL_USE_SSL` and `EMAIL_USE_TLS` are dynamically driven by `.env` (enabling Hostinger's standard Port 465 SSL or Port 587 TLS).
- [ ] **Item 63 — Canonical Brand & Template Email Standardization**: Update `leads/constants.py` and email templates to set `admin@digipandaacademy.com` and `www.digipandaacademy.com`.
- [ ] **Item 64 — Enhanced Hostinger SMTP Diagnostic Tool**: Update `leads/management/commands/test_smtp_email.py` to auto-detect Hostinger and provide specific 465 SSL vs 587 TLS diagnostics with actionable guidance.
- [ ] **Item 65 — Mailbox Credentials Verification & Live Test Send**: Test and verify live dispatch once valid Hostinger password is provided.
"""

if "## Track G: Hostinger Mailbox Integration" not in text:
    text += track_g
    with open(todo_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("TODO.md updated with Track G!")
else:
    print("Track G already in TODO.md")
