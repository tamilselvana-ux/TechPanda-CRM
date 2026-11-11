import glob, os, subprocess

js_files = sorted(glob.glob(r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\static\js\*.js'))
print(f"Scanning {len(js_files)} JS files...")
for f in js_files:
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        for i, line in enumerate(fp, 1):
            if 'tabindex=' in line or 'role="button"' in line:
                print(f"MATCH: {os.path.basename(f)}:{i} -> {line.strip()}")

# Also check Chrome parse/runtime errors across ALL base-loaded scripts
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
scripts_html = "\n".join(f'<script src="file:///{f.replace(os.sep, "/")}"></script>' for f in js_files)
test_html = f"""<!DOCTYPE html><html><head><script>
window._jsErrs = [];
window.addEventListener('error', function(e) {{
  window._jsErrs.push((e.filename || '') + ':' + e.lineno + ' -> ' + e.message);
}}, true);
</script></head><body>{scripts_html}
<script>
window.addEventListener('load', function() {{
  var p = document.createElement('pre');
  p.id = 'ERRS';
  p.textContent = JSON.stringify(window._jsErrs, null, 2);
  document.body.appendChild(p);
}});
</script></body></html>"""

tmp = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\scratch\_tmp_js_scan.html'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(test_html)

import re
out = subprocess.check_output([
    CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
    "--virtual-time-budget=2000", "--dump-dom", tmp
], stderr=subprocess.PIPE).decode('utf-8', errors='ignore')

m = re.search(r'<pre id="ERRS">(.*?)</pre>', out, re.S)
print("CHROME JS PARSE CHECK:\n", m.group(1) if m else "NOT FOUND")
if os.path.exists(tmp):
    os.remove(tmp)
