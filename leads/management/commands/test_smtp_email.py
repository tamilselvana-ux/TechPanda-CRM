import socket
import smtplib
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


class Command(BaseCommand):
    help = "Diagnose Hostinger/SMTP connectivity, authentication (SSL & TLS), and optionally send a test message."

    def add_arguments(self, parser):
        parser.add_argument(
            '--send-to',
            type=str,
            dest='send_to',
            default='',
            help='Specify an email address to send a real test email to.'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== DigiPanda CRM Hostinger / SMTP Configuration Diagnostic ==="))

        host = getattr(settings, 'EMAIL_HOST', 'smtp.hostinger.com')
        port = int(getattr(settings, 'EMAIL_PORT', 465))
        use_tls = bool(getattr(settings, 'EMAIL_USE_TLS', False))
        use_ssl = bool(getattr(settings, 'EMAIL_USE_SSL', True))
        user = getattr(settings, 'EMAIL_HOST_USER', '')
        password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        timeout = int(getattr(settings, 'EMAIL_TIMEOUT', 20))

        # 1. Print configuration summary safely
        self.stdout.write(f"EMAIL_BACKEND   : {getattr(settings, 'EMAIL_BACKEND', '')}")
        self.stdout.write(f"EMAIL_HOST      : {host}")
        self.stdout.write(f"EMAIL_PORT      : {port}")
        self.stdout.write(f"EMAIL_USE_SSL   : {use_ssl}")
        self.stdout.write(f"EMAIL_USE_TLS   : {use_tls}")
        self.stdout.write(f"EMAIL_HOST_USER : {user if user else '<NOT SET>'}")
        self.stdout.write(f"EMAIL_HOST_PASSWORD: {'[CONFIGURED]' if bool(password) else '<NOT SET / EMPTY>'}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL : {from_email}")
        self.stdout.write(f"EMAIL_TIMEOUT   : {timeout}s")
        self.stdout.write("")

        if use_tls and use_ssl:
            self.stdout.write(self.style.ERROR("[!] Warning: Both EMAIL_USE_TLS and EMAIL_USE_SSL are True. SMTP requires TLS on 587 or SSL on 465, not both."))

        # 2. Network socket check
        self.stdout.write(f"Step 1: Checking TCP socket connectivity to {host}:{port}...")
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
            self.stdout.write(self.style.SUCCESS(f"  [OK] Successfully connected to {host}:{port}."))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  [FAIL] Cannot connect to {host}:{port}: {exc}"))
            return

        # 3. SMTP handshake & Authentication check
        self.stdout.write(f"Step 2: Checking SMTP handshake and authentication ({'SSL' if use_ssl else 'TLS'})...")
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(host, port, timeout=timeout)
            else:
                server = smtplib.SMTP(host, port, timeout=timeout)

            server.ehlo()
            if use_tls and not use_ssl:
                server.starttls()
                server.ehlo()

            if user and password:
                server.login(user, password)
                self.stdout.write(self.style.SUCCESS("  [OK] SMTP authentication successful with Hostinger."))
            elif not user or not password:
                self.stdout.write(self.style.WARNING("  [SKIP] EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not set. Skipping authentication check."))

            server.quit()
        except smtplib.SMTPAuthenticationError as auth_err:
            self.stdout.write(self.style.ERROR(f"  [FAIL] SMTP Authentication failed: {auth_err.smtp_code} - {auth_err.smtp_error}"))
            self.stdout.write(self.style.NOTICE("  -> Hostinger Guidance: Confirm the mailbox password in Hostinger hPanel -> Emails -> Manage."))
            return
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  [FAIL] SMTP connection or handshake failed: {exc}"))
            return

        # 4. Optional test message dispatch
        send_to = options.get('send_to', '').strip()
        if send_to:
            self.stdout.write(f"Step 3: Sending actual test message to '{send_to}'...")
            try:
                subject = "DigiPanda Academy — SMTP Test Message"
                body = "This is a diagnostic test message sent from DigiPanda CRM verifying Hostinger SMTP delivery."
                html = """<div style="font-family: sans-serif; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                    <h2 style="color: #0284c7; margin-top: 0;">DigiPanda Academy</h2>
                    <p>This is a diagnostic test message verifying official Hostinger SMTP delivery from <strong>admin@digipandaacademy.com</strong>.</p>
                    <p style="color: #16a34a; font-weight: bold;">✔ All SMTP settings and SSL handshakes are verified.</p>
                </div>"""

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=body,
                    from_email=from_email or user,
                    to=[send_to]
                )
                msg.attach_alternative(html, "text/html")
                sent_count = msg.send(fail_silently=False)
                if sent_count > 0:
                    self.stdout.write(self.style.SUCCESS(f"  [OK] Test email successfully delivered via Hostinger SMTP to '{send_to}'."))
                else:
                    self.stdout.write(self.style.WARNING(f"  [WARNING] send() returned {sent_count}."))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"  [FAIL] Failed sending test message: {exc}"))
        else:
            self.stdout.write("Step 3: Test email dispatch skipped (use --send-to your_email@domain.com to send a live test message).")

        self.stdout.write(self.style.SUCCESS("\nDiagnostic complete."))
