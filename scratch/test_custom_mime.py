import os, sys
sys.path.insert(0, r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.core.mail import get_connection, EmailMessage
from email.mime.multipart import MIMEMultipart

class CustomMIMEEmail(EmailMessage):
    def __init__(self, mime_message, to=None, from_email=None):
        super().__init__(to=to, from_email=from_email)
        self._mime_message = mime_message

    def message(self):
        return self._mime_message

root = MIMEMultipart('related')
root['Subject'] = 'Test'
root['From'] = 'admin@digipandaacademy.com'
root['To'] = 'test@example.com'
c = CustomMIMEEmail(root, to=['test@example.com'], from_email='admin@digipandaacademy.com')
print('Message callable returns root:', c.message() is root)
