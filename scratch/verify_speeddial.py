import sys, os
sys.path.insert(0, r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.test import Client
from accounts.models import User, UserRole

client = Client()
tc = User.objects.filter(role=UserRole.TELECALLER).first()
client.force_login(tc)
res = client.get('/telecaller/leads/')
assert res.status_code == 200, f'Expected 200 got {res.status_code}'
content = res.content.decode('utf-8')
assert 'tp-quick-disposition-wrap' in content, 'Quick disposition wrap missing'
assert 'data-hotkey="1"' in content, 'Hotkey 1 button missing'
assert 'telecaller-speeddial.js' in content, 'Speeddial script missing'
print('✅ Telecaller leads page verified with 1-click speeddial toolbar and script!')
