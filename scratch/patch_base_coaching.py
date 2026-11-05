import os

path = 'templates/base.html' if os.path.exists('templates/base.html') else 'CRM/templates/base.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add AI Objection Coach Panel in Call Modal
coach_panel = """                <!-- Real-Time AI Objection Coach Panel (Phase 5, Item 150) -->
                <div class="ai-objection-coach-panel" style="background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%); border: 1px solid #a7f3d0; border-radius: 8px; padding: 12px 14px; margin-bottom: 14px;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #065f46; display: flex; align-items: center; gap: 6px;">
                      <span>🤖 Live AI Objection Coach:</span>
                    </span>
                    <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                      <button type="button" class="btn btn-sm" onclick="triggerObjectionCoach('FEE_HIGH')" style="padding: 2px 7px; font-size: 0.72rem; background: #fff; border: 1px solid #cbd5e1; border-radius: 4px; font-weight: 600; cursor: pointer;">💰 Fees</button>
                      <button type="button" class="btn btn-sm" onclick="triggerObjectionCoach('PLACEMENT_DOUBT')" style="padding: 2px 7px; font-size: 0.72rem; background: #fff; border: 1px solid #cbd5e1; border-radius: 4px; font-weight: 600; cursor: pointer;">💼 Job/Placement</button>
                      <button type="button" class="btn btn-sm" onclick="triggerObjectionCoach('TIMING_CLASH')" style="padding: 2px 7px; font-size: 0.72rem; background: #fff; border: 1px solid #cbd5e1; border-radius: 4px; font-weight: 600; cursor: pointer;">⏰ Timings</button>
                      <button type="button" class="btn btn-sm" onclick="triggerObjectionCoach('COMPETITOR_COMPARISON')" style="padding: 2px 7px; font-size: 0.72rem; background: #fff; border: 1px solid #cbd5e1; border-radius: 4px; font-weight: 600; cursor: pointer;">🆚 Compare</button>
                      <button type="button" class="btn btn-sm" onclick="triggerObjectionCoach('NOT_SURE')" style="padding: 2px 7px; font-size: 0.72rem; background: #fff; border: 1px solid #cbd5e1; border-radius: 4px; font-weight: 600; cursor: pointer;">🤷 Confused</button>
                    </div>
                  </div>

                  <!-- Live Coach Response Card -->
                  <div id="aiCoachCard" style="display: none; background: #ffffff; border: 1px solid #86efac; border-radius: 6px; padding: 10px 12px; margin-top: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                      <div id="aiCoachTitle" style="font-size: 0.82rem; font-weight: 700; color: #1e293b;"></div>
                      <button type="button" id="btnInsertCoachNote" onclick="insertCoachingIntoNotes()" style="background: #059669; color: #fff; border: none; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; cursor: pointer;">
                        📋 Paste to Notes
                      </button>
                    </div>
                    <div id="aiCoachRebuttal" style="font-size: 0.8rem; color: #047857; margin-bottom: 6px; line-height: 1.4;"></div>
                    <ul id="aiCoachPoints" style="margin: 0; padding-left: 18px; font-size: 0.75rem; color: #334155; line-height: 1.4;"></ul>
                    <div id="aiCoachAction" style="font-size: 0.75rem; color: #1e40af; margin-top: 6px; font-weight: 600;"></div>
                  </div>
                </div>
"""

target_disp = '<div class="tp-quick-disposition-wrap"'
if target_disp in html and "ai-objection-coach-panel" not in html:
    html = html.replace(target_disp, coach_panel + "\n                " + target_disp, 1)
    print("Inserted AI Coach Panel into call modal")

# 2. Add script tag
target_speeddial_script = '<script src="{% static \'js/telecaller-speeddial.js\' %}"></script>'
new_coaching_script = """<script src="{% static 'js/telecaller-speeddial.js' %}"></script>
  <!-- Real-Time AI Objection Coaching Engine -->
  <script src="{% static 'js/telecaller-coaching.js' %}?v=20261105"></script>"""

if target_speeddial_script in html and "telecaller-coaching.js" not in html:
    html = html.replace(target_speeddial_script, new_coaching_script, 1)
    print("Added telecaller-coaching.js script tag")

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("BASE_HTML_COACHING_PATCHED")
