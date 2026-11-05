import os

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\base.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target_btn = """          <!-- 3D Isometric Theme Toggle Coin -->"""

replacement_btn = """          <!-- On Duty / Out of Office Toggle (Phase 1, Item 140) -->
          {% if user.is_authenticated and user.role in "TELECALLER COUNSELOR" %}
          <button type="button" 
                  id="tp-duty-toggle-btn" 
                  class="tp-duty-toggle-btn {% if user.is_on_duty %}on-duty{% else %}out-of-office{% endif %}"
                  title="Click to toggle your allocation availability: On Duty vs Out of Office"
                  style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; cursor: pointer; transition: all 0.2s ease; border: 1px solid {% if user.is_on_duty %}rgba(16, 185, 129, 0.4){% else %}rgba(239, 68, 68, 0.4){% endif %}; background: {% if user.is_on_duty %}rgba(16, 185, 129, 0.12){% else %}rgba(239, 68, 68, 0.12){% endif %}; color: {% if user.is_on_duty %}#059669{% else %}#dc2626{% endif %}; margin-right: 6px;">
            <span class="tp-duty-dot" style="width: 8px; height: 8px; border-radius: 50%; background: {% if user.is_on_duty %}#10b981{% else %}#ef4444{% endif %}; display: inline-block;"></span>
            <span id="tp-duty-text">{% if user.is_on_duty %}On Duty{% else %}Out of Office{% endif %}</span>
          </button>
          {% endif %}

          <!-- 3D Isometric Theme Toggle Coin -->"""

assert target_btn in content, "target_btn not found in base.html"
content = content.replace(target_btn, replacement_btn, 1)

target_js = """  <!-- 3D Cinematic Interactive Micro-Engine -->"""

replacement_js = """  <script>
    document.addEventListener('DOMContentLoaded', function() {
      var dutyBtn = document.getElementById('tp-duty-toggle-btn');
      if (dutyBtn) {
        dutyBtn.addEventListener('click', function() {
          dutyBtn.disabled = true;
          fetch("{% url 'toggle_duty_status' %}", {
            method: 'POST',
            headers: {
              'X-CSRFToken': window.getCsrfToken(),
              'Content-Type': 'application/json'
            }
          })
          .then(function(res) { return res.json(); })
          .then(function(data) {
            dutyBtn.disabled = false;
            if (data.success) {
              var textSpan = document.getElementById('tp-duty-text');
              var dotSpan = dutyBtn.querySelector('.tp-duty-dot');
              if (data.is_on_duty) {
                dutyBtn.className = 'tp-duty-toggle-btn on-duty';
                dutyBtn.style.background = 'rgba(16, 185, 129, 0.12)';
                dutyBtn.style.borderColor = 'rgba(16, 185, 129, 0.4)';
                dutyBtn.style.color = '#059669';
                if (dotSpan) dotSpan.style.background = '#10b981';
                if (textSpan) textSpan.textContent = 'On Duty';
              } else {
                dutyBtn.className = 'tp-duty-toggle-btn out-of-office';
                dutyBtn.style.background = 'rgba(239, 68, 68, 0.12)';
                dutyBtn.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                dutyBtn.style.color = '#dc2626';
                if (dotSpan) dotSpan.style.background = '#ef4444';
                if (textSpan) textSpan.textContent = 'Out of Office';
              }
            }
          })
          .catch(function(err) {
            dutyBtn.disabled = false;
            console.error('Failed to toggle duty status', err);
          });
        });
      }
    });
  </script>
  <!-- 3D Cinematic Interactive Micro-Engine -->"""

assert target_js in content, "target_js not found in base.html"
content = content.replace(target_js, replacement_js, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated base.html with Duty Status toggle button and handler")
