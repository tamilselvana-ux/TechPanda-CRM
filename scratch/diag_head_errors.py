import os, re, subprocess, django, sys
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

STATIC_URI = "file:///d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM/static/"
html = re.sub(r'(/static/[^"\'\s?]+)\?[^"\'\s]*', r'\1', html)
html = html.replace('href="/static/', f'href="{STATIC_URI}').replace('src="/static/', f'src="{STATIC_URI}')

# Inject error listener in <head> BEFORE any script loads
head_err = """
<script>
window._earlyErrors = [];
window.addEventListener('error', function(e) {
  window._earlyErrors.push({
    message: e.message,
    filename: e.filename,
    lineno: e.lineno,
    colno: e.colno
  });
}, true);
</script>
"""
html = html.replace('<head>', '<head>' + head_err)

# Also check if crm.js functions exist and check CSS files
diag_js = """
<script>
window.addEventListener('DOMContentLoaded', function() {
  setTimeout(function() {
    var out = document.createElement('pre');
    out.id = 'DIAG_HEAD_RESULT';
    out.textContent = JSON.stringify({
      earlyErrors: window._earlyErrors,
      openCallDialerExists: typeof window.openCallDialer,
      crmLoaded: !!document.cookie.match(/django_timezone/)
    }, null, 2);
    document.body.prepend(out);
  }, 300);
});
</script>
"""
html = html.replace('</body>', diag_js + '</body>')

tmp = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\scratch\_diag_head.html'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(html)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
out = subprocess.check_output([
    CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
    "--virtual-time-budget=2000", "--dump-dom", tmp
], stderr=subprocess.PIPE).decode('utf-8', errors='ignore')

m = re.search(r'<pre id="DIAG_HEAD_RESULT">(.*?)</pre>', out, re.S)
print("DIAG HEAD RESULT:\n", m.group(1) if m else "NOT FOUND")
if os.path.exists(tmp):
    os.remove(tmp)
