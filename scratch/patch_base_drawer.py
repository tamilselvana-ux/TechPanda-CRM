import os

path = 'templates/base.html' if os.path.exists('templates/base.html') else 'CRM/templates/base.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

target = '<!-- 3D Cinematic Interactive Micro-Engine -->'
insertion = """  <!-- Unified 360° Student Admissions Slide-over Drawer Component -->
  {% include 'components/student_360_drawer.html' %}
  <script src="{% static 'js/student-360-drawer.js' %}?v=20261105"></script>

  """

if target in html and "student_360_drawer.html" not in html:
    html = html.replace(target, insertion + target, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("PATCHED_BASE_HTML_DRAWER")
else:
    print("ALREADY_PATCHED_OR_TARGET_NOT_FOUND")
