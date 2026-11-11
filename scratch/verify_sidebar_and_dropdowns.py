import os, re, subprocess, json, django, sys
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

head_err = """
<script>
window._earlyErrors = [];
window.addEventListener('error', function(e) {
  window._earlyErrors.push({message: e.message, filename: e.filename, lineno: e.lineno});
}, true);
</script>
"""
html = html.replace('<head>', '<head>' + head_err)

diag_js = """
<script>
window.addEventListener('DOMContentLoaded', function() {
  setTimeout(function() {
    var groups = ['admin-team-nav', 'admin-comms-nav', 'admin-finance-nav', 'admin-setup-nav'];
    var results = {};
    groups.forEach(function(id) {
      var h = document.querySelector('[data-target="' + id + '"]');
      var c = document.getElementById(id);
      if (h && c) {
        var before = getComputedStyle(c).display;
        h.click(); // open
        var afterOpen = getComputedStyle(c).display;
        var hasOpenClass = c.classList.contains('open');
        h.click(); // close back
        var afterClose = getComputedStyle(c).display;
        results[id] = { before: before, afterOpen: afterOpen, hasOpenClass: hasOpenClass, afterClose: afterClose };
      }
    });
    // Leave Team & Staff open for visual screenshot verification
    var teamHeader = document.querySelector('[data-target="admin-team-nav"]');
    if (teamHeader) teamHeader.click();

    var pre = document.createElement('pre');
    pre.id = 'VERIFY_DROPDOWNS';
    pre.textContent = JSON.stringify({
      errors: window._earlyErrors,
      openCallDialerExists: typeof window.openCallDialer,
      sidebarAccordions: results
    }, null, 2);
    document.body.prepend(pre);
  }, 400);
});
</script>
"""
html = html.replace('</body>', diag_js + '</body>')

tmp = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\scratch\_tmp_verify_sidebar.html'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(html)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
out_dom = subprocess.check_output([
    CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
    "--virtual-time-budget=2000", "--dump-dom", tmp
], stderr=subprocess.PIPE).decode('utf-8', errors='ignore')

m = re.search(r'<pre id="VERIFY_DROPDOWNS">(.*?)</pre>', out_dom, re.S)
assert m, "VERIFY_DROPDOWNS missing"
data = json.loads(m.group(1))
print("VERIFY DROPDOWNS JSON:\n", json.dumps(data, indent=2))
assert data["errors"] == [], f"Unexpected JS errors: {data['errors']}"
assert data["openCallDialerExists"] == "function", "openCallDialer must be defined"
for g_id, st in data["sidebarAccordions"].items():
    assert st["afterOpen"] == "block" and st["hasOpenClass"] is True, f"{g_id} failed to open!"
    assert st["afterClose"] == "none", f"{g_id} failed to close!"

# Also capture visual PNG of sidebar opened
out_png = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\scratch\verify_sidebar_open.png'
subprocess.run([
    CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
    "--virtual-time-budget=2000", "--window-size=1280,820", f"--screenshot={out_png}", tmp
], capture_output=True)

if os.path.exists(tmp):
    os.remove(tmp)
print(f"ALL SIDEBAR DROPDOWN CHECKS PASSED! Screenshot saved: {out_png}")
