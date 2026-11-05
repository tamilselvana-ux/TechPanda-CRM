import os

path = 'templates/leads/enrollment_form.html' if os.path.exists('templates/leads/enrollment_form.html') else 'CRM/templates/leads/enrollment_form.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add hidden installment_method input
target_split = '<div id="splitPaymentSettings"'
replacement_split = """<div id="splitPaymentSettings"
        <input type="hidden" name="installment_method" id="id_installment_method" value="MANUAL">"""

if target_split in html and "id_installment_method" not in html:
    html = html.replace(target_split, replacement_split, 1)
    print("Added id_installment_method input")

# 2. Add Equalize Remaining button in header
target_header = """          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 0.8rem; font-weight: 700; color: var(--tp-text-primary); text-transform: uppercase;">
              Projected Installment Schedule
            </span>
            <span style="font-size: 0.75rem; color: #10b981; font-weight: 600;">
              Total Scheduled: <span id="previewScheduledTotal" style="font-variant-numeric: tabular-nums;">₹0.00</span>
            </span>
          </div>"""

replacement_header = """          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
            <span style="font-size: 0.8rem; font-weight: 700; color: var(--tp-text-primary); text-transform: uppercase;">
              Dynamic Installment Balancing Matrix
            </span>
            <div style="display: flex; gap: 8px; align-items: center;">
              <button type="button" class="btn btn-sm btn-secondary" onclick="equalizeAllInstallments()" style="padding: 3px 10px; font-size: 0.72rem; font-weight: 700; border-radius: 4px;">
                ⚡ Equalize Remaining
              </button>
              <span id="previewScheduledTotal" style="font-size: 0.75rem; font-weight: 600;">
                Total Scheduled: ₹0.00
              </span>
            </div>
          </div>"""

if target_header in html:
    html = html.replace(target_header, replacement_header, 1)
    print("Added Dynamic Matrix header and Equalize button")

# 3. Add script tag for installment-calculator.js
script_tag = """{% load static %}
<script src="{% static 'js/installment-calculator.js' %}?v=20261105"></script>
<script>"""

if '<script>' in html and 'installment-calculator.js' not in html:
    html = html.replace('<script>', script_tag, 1)
    print("Added installment-calculator.js script tag")

# 4. In recalculateGST call initInstallmentEngine
target_optimistic = "  document.getElementById('previewTotal').textContent = formatINR(optimistic.total);"
replacement_optimistic = """  document.getElementById('previewTotal').textContent = formatINR(optimistic.total);
  if (typeof initInstallmentEngine === 'function') {
    initInstallmentEngine(optimistic.total, instCount, firstDate);
  }"""

if target_optimistic in html and "initInstallmentEngine" not in html:
    html = html.replace(target_optimistic, replacement_optimistic, 1)
    print("Integrated initInstallmentEngine into recalculateGST")

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("ENROLLMENT_FORM_PATCHED_SUCCESSFULLY")
