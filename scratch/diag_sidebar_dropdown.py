import os, subprocess, django, sys
sys.path.insert(0, r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.filter(role='ADMIN', is_active=True).first() or User.objects.filter(is_superuser=True).first()
client = Client()
client.force_login(admin)
resp = client.get('/admin/dashboard/')
html = resp.content.decode('utf-8', errors='ignore')

# Point static to local disk
STATIC_URI = "file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/static/"
import re
html = re.sub(r'(/static/[^"\'\s?]+)\?[^"\'\s]*', r'\1', html)
html = html.replace('href="/static/', f'href="{STATIC_URI}').replace('src="/static/', f'src="{STATIC_URI}')

# Inject diagnostic script right before </body>
diag_js = """
<script>
window._diagErrors = [];
window.onerror = function(msg, url, line) { window._diagErrors.push(msg + ' @ ' + url + ':' + line); };
window.addEventListener('DOMContentLoaded', function() {
  setTimeout(function() {
    var header = document.querySelector('[data-target="admin-team-nav"]');
    var target = document.getElementById('admin-team-nav');
    var beforeClass = target ? target.className : 'NO_TARGET';
    var beforeDisplay = target ? getComputedStyle(target).display : 'NO_TARGET';
    if (header) header.click();
    var afterClass = target ? target.className : 'NO_TARGET';
    var afterDisplay = target ? getComputedStyle(target).display : 'NO_TARGET';
    var out = document.createElement('pre');
    out.id = 'DIAG_RESULT';
    out.textContent = JSON.stringify({
      errors: window._diagErrors,
      headerFound: !!header,
      beforeClass: beforeClass,
      beforeDisplay: beforeDisplay,
      afterClass: afterClass,
      afterDisplay: afterDisplay,
      pointerEventsHeader: header ? getComputedStyle(header).pointerEvents : null,
      pointerEventsSidebar: document.querySelector('.app-sidebar') ? getComputedStyle(document.querySelector('.app-sidebar')).pointerEvents : null
    }, null, 2);
    document.body.prepend(out);
  }, 400);
});
</script>
"""
html = html.replace('</body>', diag_js + '</body>')
tmp = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\scratch\_diag_sidebar.html'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(html)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
out = subprocess.check_output([
    CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
    "--virtual-time-budget=2000", "--dump-dom", tmp
], stderr=subprocess.PIPE).decode('utf-8', errors='ignore')

m = re.search(r'<pre id="DIAG_RESULT">(.*?)</pre>', out, re.S)
print("DIAG RESULT:\n", m.group(1) if m else "DIAG_RESULT NOT FOUND")
if os.path.exists(tmp):
    os.remove(tmp)
