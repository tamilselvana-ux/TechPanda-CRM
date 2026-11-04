import os, sys
sys.path.insert(0, r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage

msg = EmailMultiAlternatives('Subject', 'Text body', 'admin@digipandaacademy.com', ['test@example.com'])
msg.mixed_subtype = 'related'
msg.attach_alternative('<html><body><img src="cid:test_logo"></body></html>', 'text/html')
mime_img = MIMEImage(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82', _subtype='png')
mime_img.add_header('Content-ID', '<test_logo>')
mime_img.add_header('Content-Disposition', 'inline', filename='test_logo.png')
msg.attach(mime_img)

raw = msg.message().as_string()
print('\n'.join(raw.splitlines()[:60]))
