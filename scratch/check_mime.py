import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import sys; sys.path.insert(0, 'CRM_Integrated_v2/CRM')
django.setup()
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage

msg = EmailMultiAlternatives('Test', 'Text body', 'admin@digipandaacademy.com', ['test@example.com'])
msg.mixed_subtype = 'related'
msg.attach_alternative('<html><body><img src="cid:test_logo"></body></html>', 'text/html')
with open('CRM_Integrated_v2/CRM/static/images/digipanda_logo.png', 'rb') as f:
    mime_img = MIMEImage(f.read())
mime_img.add_header('Content-ID', '<test_logo>')
mime_img.add_header('Content-Disposition', 'inline', filename='test_logo.png')
msg.attach(mime_img)
msg.attach('invoice.pdf', b'%PDF-1.4 fake pdf', 'application/pdf')

m = msg.message()
print('Content-Type:', m.get_content_type())
for part in m.walk():
    print(' - Part:', part.get_content_type(), '| Content-ID:', part.get('Content-ID'), '| Disposition:', part.get('Content-Disposition'))
