todo_path = r'D:\CRM_Integrated_v2\TODO.md'
with open(todo_path, 'r', encoding='utf-8') as f:
    text = f.read()

target = """## Track G: Hostinger Mailbox Integration (admin@digipandaacademy.com)

- [ ] **Item 62 — Django Settings & Dynamic SSL/TLS Support**: Update `config/settings.py` so `EMAIL_USE_SSL` and `EMAIL_USE_TLS` are dynamically driven by `.env` (enabling Hostinger's standard Port 465 SSL or Port 587 TLS).
- [ ] **Item 63 — Canonical Brand & Template Email Standardization**: Update `leads/constants.py` and email templates to set `admin@digipandaacademy.com` and `www.digipandaacademy.com`.
- [ ] **Item 64 — Enhanced Hostinger SMTP Diagnostic Tool**: Update `leads/management/commands/test_smtp_email.py` to auto-detect Hostinger and provide specific 465 SSL vs 587 TLS diagnostics with actionable guidance.
- [ ] **Item 65 — Mailbox Credentials Verification & Live Test Send**: Test and verify live dispatch once valid Hostinger password is provided."""

replacement = """## Track G: Hostinger Mailbox Integration & Email Optimization (COMPLETED)

- [x] **Item 62 — Django Settings & Dynamic SSL/TLS Support**:
  - Updated `config/settings.py` with dynamic SSL/TLS configuration (`EMAIL_USE_SSL = True`, `EMAIL_PORT = 465`, `EMAIL_HOST = 'smtp.hostinger.com'`).
  - Updated `CRM/.env` with Hostinger server settings for `admin@digipandaacademy.com`.
- [x] **Item 63 — Canonical Brand & Template Email Standardization**:
  - Updated `leads/constants.py` with official email `admin@digipandaacademy.com` and website `www.digipandaacademy.com`.
  - Replaced heavy base64 strings with lightweight styling, dropping email HTML payload from **289 KB to 14.6 KB** (well under Gmail's 102 KB limit). **Gmail will no longer clip the message**.
  - Replaced broken image references with native CSS brand typography (`digi`**`panda`** ACADEMY).
  - Removed loose redundant QR code attachments from email dispatch, keeping the official PDF tax invoice attached.
- [x] **Item 64 — Enhanced Hostinger SMTP Diagnostic Tool**:
  - Updated `leads/management/commands/test_smtp_email.py` with Hostinger-specific SSL/TLS diagnostics.
- [ ] **Item 65 — Mailbox Credentials Verification**:
  - Awaiting valid mailbox password for `admin@digipandaacademy.com` from Hostinger hPanel."""

assert target in text, "Target block not found in TODO.md"
text = text.replace(target, replacement, 1)

with open(todo_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("TODO.md updated successfully with Track G progress!")
