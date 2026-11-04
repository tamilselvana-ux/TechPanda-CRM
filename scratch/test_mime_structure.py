import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import sys; sys.path.insert(0, 'CRM_Integrated_v2/CRM')
django.setup()

from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage

msg = EmailMultiAlternatives(subject='Test', body='Text version', from_email='admin@digipandaacademy.com', to=['test@example.com'])
msg.attach_alternative('<html><body><img src="cid:digipanda_logo"></body></html>', 'text/html')
msg.mixed_subtype = 'related'

with open('CRM_Integrated_v2/CRM/static/images/digipanda_email_logo.png', 'rb') as f:
    img = MIMEImage(f.read(), _subtype='png')
img.add_header('Content-ID', '<digipanda_logo>')
img.add_header('Content-Disposition', 'inline', filename='digipanda_logo.png')
msg.attach(img)

m = msg.message()
print('Top level Content-Type:', m.get_content_type())
for i, part in enumerate(m.walk()):
    print(f'Part {i}: {part.get_content_type()} | CID: {part.get("Content-ID")} | Disposition: {part.get("Content-Disposition")}')
