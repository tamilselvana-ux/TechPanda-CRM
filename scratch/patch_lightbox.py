import os

path = 'templates/accountant/verification_list.html' if os.path.exists('templates/accountant/verification_list.html') else 'CRM/templates/accountant/verification_list.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Enhance proof column button
old_proof_block = """              {% if p.payment_proof %}
              <a href="{% url 'accountant_payment_proof_view' p.id %}" target="_blank" class="btn btn-sm btn-outline-info" style="padding: 3px 8px; font-size: 0.75rem; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                <span>Proof ↗</span>
              </a>
              {% else %}"""

new_proof_block = """              {% if p.payment_proof %}
              <div style="display: flex; gap: 4px; align-items: center;">
                <button type="button" class="btn btn-sm" style="padding: 3px 8px; font-size: 0.74rem; font-weight: 700; color: #fff; background: #0284c7; border: none; border-radius: 4px; display: inline-flex; align-items: center; gap: 4px; cursor: pointer;" onclick="openProofLightbox('{% url 'accountant_payment_proof_view' p.id %}', '{{ p.receipt_number|escapejs }}', '{{ p.transaction_reference|escapejs }}', '{{ p.enrollment.student_name|escapejs }}', '{{ p.amount }}')">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                  <span>Inspect</span>
                </button>
                <a href="{% url 'accountant_payment_proof_view' p.id %}" target="_blank" class="btn btn-sm btn-outline-secondary" style="padding: 3px 6px; font-size: 0.72rem;" title="Open raw file in new tab">↗</a>
              </div>
              {% else %}"""

if old_proof_block in html:
    html = html.replace(old_proof_block, new_proof_block, 1)
    print("Replaced proof button in table")
else:
    print("old_proof_block not found")

# 2. Add Lightbox Modal markup
lightbox_modal = """
<!-- HIGH-RESOLUTION PROOF INSPECTION LIGHTBOX MODAL -->
<div id="proofLightboxModal" style="display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(8px); z-index: 99999; flex-direction: column;">
  <!-- Lightbox Header / Toolbar -->
  <div style="padding: 12px 24px; background: rgba(30, 41, 59, 0.95); border-bottom: 1px solid rgba(255,255,255,0.12); display: flex; justify-content: space-between; align-items: center; color: #fff; flex-wrap: wrap; gap: 10px;">
    <div id="lightboxStudentInfo" style="font-size: 0.92rem; color: #f1f5f9;"></div>

    <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
      <span style="font-size: 0.8rem; color: #94a3b8; margin-right: 4px;">UTR: <code id="lightboxUtrText" style="color: #38bdf8; font-weight: 700; background: rgba(0,0,0,0.35); padding: 3px 8px; border-radius: 4px; font-family: monospace;"></code></span>
      <button type="button" id="btnCopyLightboxUtr" onclick="copyLightboxUTR()" class="btn btn-sm" style="background: rgba(255,255,255,0.15); color: #fff; border: 1px solid rgba(255,255,255,0.25); font-size: 0.72rem; padding: 3px 8px; border-radius: 4px; cursor: pointer;">Copy UTR</button>

      <div style="height: 18px; width: 1px; background: rgba(255,255,255,0.2); margin: 0 4px;"></div>

      <button type="button" onclick="zoomLightbox(0.5)" class="btn btn-sm" style="background: rgba(255,255,255,0.15); color: #fff; font-weight: 700; padding: 3px 9px; border-radius: 4px; cursor: pointer;" title="Zoom In (+)">➕</button>
      <span id="lightboxZoomLevel" style="font-size: 0.78rem; font-family: monospace; color: #38bdf8; min-width: 44px; text-align: center; font-weight: 700;">100%</span>
      <button type="button" onclick="zoomLightbox(-0.5)" class="btn btn-sm" style="background: rgba(255,255,255,0.15); color: #fff; font-weight: 700; padding: 3px 9px; border-radius: 4px; cursor: pointer;" title="Zoom Out (-)">➖</button>
      <button type="button" onclick="rotateLightbox()" class="btn btn-sm" style="background: rgba(255,255,255,0.15); color: #fff; font-weight: 600; padding: 3px 10px; border-radius: 4px; cursor: pointer;" title="Rotate 90° Clockwise">🔄 Rotate</button>
      <button type="button" id="btnToggleContrast" onclick="toggleContrastLightbox()" class="btn btn-sm" style="background: rgba(255,255,255,0.15); color: #fff; font-weight: 600; padding: 3px 10px; border-radius: 4px; cursor: pointer;" title="Toggle Contrast Filter">🌓 Contrast</button>
      <button type="button" onclick="resetLightbox()" class="btn btn-sm" style="background: rgba(255,255,255,0.15); color: #fff; font-weight: 600; padding: 3px 10px; border-radius: 4px; cursor: pointer;" title="Reset Scale">Reset</button>

      <button type="button" onclick="closeProofLightbox()" style="background: transparent; border: none; color: #ef4444; font-size: 1.8rem; cursor: pointer; line-height: 1; padding: 0 8px; margin-left: 8px;" title="Close (Esc)">&times;</button>
    </div>
  </div>

  <!-- Zoom Viewport with Drag Support -->
  <div id="lightboxViewport" style="flex: 1; overflow: hidden; display: flex; align-items: center; justify-content: center; position: relative; cursor: grab; user-select: none; padding: 20px;">
    <img id="lightboxProofImg" src="" alt="Payment Proof Screenshot" style="max-width: 90%; max-height: 82vh; object-fit: contain; border-radius: 8px; box-shadow: 0 15px 50px rgba(0,0,0,0.6); transition: transform 0.15s ease-out, filter 0.2s ease;">
  </div>
</div>

{% load static %}
<script src="{% static 'js/verification-lightbox.js' %}?v=20261105"></script>
"""

target_end_modal = '<!-- Rejection Modal with Mandatory Comment -->'
if target_end_modal in html and "proofLightboxModal" not in html:
    html = html.replace(target_end_modal, lightbox_modal + "\n" + target_end_modal, 1)
    print("Inserted Lightbox modal markup")

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("LIGHTBOX_PATCHES_APPLIED")
