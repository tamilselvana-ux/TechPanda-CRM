import os

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\base.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """                <div class="form-group" style="margin-bottom: 14px;">
                  <label class="form-label" style="font-weight: 600;">Call Notes <span class="required" style="color: #dc2626;">*</span></label>"""

replacement = """                <!-- 1-Click Speed-Dial Disposition Toolbar (Phase 2, Item 142) -->
                <div class="tp-quick-disposition-wrap" style="margin-bottom: 14px;">
                  <div style="font-size: 0.75rem; font-weight: 700; color: var(--tp-text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
                    <span>⚡ Quick Dispositions (Press Key 1-5)</span>
                    <span style="font-size: 0.7rem; font-weight: 600; color: var(--tp-primary-600);">Auto-logs & Saves</span>
                  </div>
                  <div class="tp-quick-disposition-toolbar" style="display: flex; gap: 6px; flex-wrap: wrap;">
                    <button type="button" class="tp-quick-btn" data-hotkey="1" style="background: rgba(239, 68, 68, 0.1); color: #dc2626; border: 1px solid rgba(239, 68, 68, 0.35); font-weight: 700; border-radius: 6px; padding: 5px 9px; font-size: 0.75rem; display: inline-flex; align-items: center; gap: 5px; cursor: pointer;">
                      <kbd style="background: #dc2626; color: #fff; padding: 1px 5px; border-radius: 3px; font-size: 0.7rem; font-family: monospace;">1</kbd>
                      <span>RNR (No Answer)</span>
                    </button>
                    <button type="button" class="tp-quick-btn" data-hotkey="2" style="background: rgba(245, 158, 11, 0.1); color: #b45309; border: 1px solid rgba(245, 158, 11, 0.35); font-weight: 700; border-radius: 6px; padding: 5px 9px; font-size: 0.75rem; display: inline-flex; align-items: center; gap: 5px; cursor: pointer;">
                      <kbd style="background: #b45309; color: #fff; padding: 1px 5px; border-radius: 3px; font-size: 0.7rem; font-family: monospace;">2</kbd>
                      <span>Busy</span>
                    </button>
                    <button type="button" class="tp-quick-btn" data-hotkey="3" style="background: rgba(59, 130, 246, 0.1); color: #1d4ed8; border: 1px solid rgba(59, 130, 246, 0.35); font-weight: 700; border-radius: 6px; padding: 5px 9px; font-size: 0.75rem; display: inline-flex; align-items: center; gap: 5px; cursor: pointer;">
                      <kbd style="background: #1d4ed8; color: #fff; padding: 1px 5px; border-radius: 3px; font-size: 0.7rem; font-family: monospace;">3</kbd>
                      <span>Callback (2h)</span>
                    </button>
                    <button type="button" class="tp-quick-btn" data-hotkey="4" style="background: rgba(100, 116, 139, 0.1); color: #475569; border: 1px solid rgba(100, 116, 139, 0.35); font-weight: 700; border-radius: 6px; padding: 5px 9px; font-size: 0.75rem; display: inline-flex; align-items: center; gap: 5px; cursor: pointer;">
                      <kbd style="background: #475569; color: #fff; padding: 1px 5px; border-radius: 3px; font-size: 0.7rem; font-family: monospace;">4</kbd>
                      <span>Not Interested</span>
                    </button>
                    <button type="button" class="tp-quick-btn" data-hotkey="5" style="background: rgba(16, 185, 129, 0.1); color: #047857; border: 1px solid rgba(16, 185, 129, 0.35); font-weight: 700; border-radius: 6px; padding: 5px 9px; font-size: 0.75rem; display: inline-flex; align-items: center; gap: 5px; cursor: pointer;">
                      <kbd style="background: #047857; color: #fff; padding: 1px 5px; border-radius: 3px; font-size: 0.7rem; font-family: monospace;">5</kbd>
                      <span>Interested 🔥</span>
                    </button>
                  </div>
                </div>

                <div class="form-group" style="margin-bottom: 14px;">
                  <label class="form-label" style="font-weight: 600;">Call Notes <span class="required" style="color: #dc2626;">*</span></label>"""

assert target in content, "target not found in base.html"
content = content.replace(target, replacement, 1)

target_js = """  <!-- Compact Date Range Picker -->
  <script src="{% static 'js/date-range-picker.js' %}?v=20261030_compact"></script>"""

replacement_js = """  <!-- Telecaller 1-Click Speed-Dial Dispositions -->
  <script src="{% static 'js/telecaller-speeddial.js' %}"></script>
  <!-- Compact Date Range Picker -->
  <script src="{% static 'js/date-range-picker.js' %}?v=20261030_compact"></script>"""

assert target_js in content, "target_js not found in base.html"
content = content.replace(target_js, replacement_js, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated base.html with Quick Dispositions toolbar and telecaller-speeddial.js")
