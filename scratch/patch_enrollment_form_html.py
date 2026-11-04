path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\leads\enrollment_form.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update form tag with enctype
html = html.replace(
    '<form method="post" action="" id="enrollmentForm">',
    '<form method="post" action="" id="enrollmentForm" enctype="multipart/form-data">'
)

# 2. Insert First Payment section before submit buttons
section_first_payment = '''      <!-- 4. OPTIONAL FIRST PAYMENT AT ENROLLMENT -->
      <div class="crm-card tp-card" style="margin-top: 20px; padding: 20px; border-radius: var(--tp-radius-md); border: 1px solid var(--tp-surface-border); background: var(--tp-surface-card);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid var(--tp-surface-border-subtle); padding-bottom: 8px;">
          <h3 style="font-size: 1.05rem; font-weight: 700; margin: 0; color: var(--tp-text-primary); display: flex; align-items: center; gap: 8px;">
            <span>4. First Payment at Enrollment</span>
            <span style="font-size: 0.78rem; font-weight: 500; color: var(--tp-text-muted);">(Optional)</span>
          </h3>
          <span class="badge" style="background: rgba(16, 185, 129, 0.12); color: #059669; font-weight: 600; font-size: 0.72rem; padding: 4px 8px; border-radius: 4px;">
            Accountant Verification
          </span>
        </div>
        <p style="font-size: 0.8rem; color: var(--tp-text-muted); margin-bottom: 14px; line-height: 1.4;">
          If the student is paying an initial installment today, enter the transaction details below. The payment will be submitted to the Accountant for ledger verification and credited to the student's account upon approval.
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 180px), 1fr)); gap: 14px;">
          <div>
            <label class="tp-label">Amount Paid (₹)</label>
            <input type="number" step="0.01" min="0" name="first_payment_amount" id="first_payment_amount" class="form-control tp-input" placeholder="e.g. 5000">
            <span id="firstPaymentHint" style="font-size: 0.72rem; color: var(--tp-text-muted); display: block; margin-top: 3px;">
              Leave blank if collecting later.
            </span>
          </div>
          <div>
            <label class="tp-label">Payment Date</label>
            <input type="date" name="first_payment_date" id="first_payment_date" class="form-control tp-input" value="{{ today_str }}">
          </div>
          <div>
            <label class="tp-label">Payment Mode</label>
            <select name="first_payment_method" id="first_payment_method" class="form-select tp-select">
              <option value="Cash">Cash</option>
              <option value="UPI" selected>UPI</option>
              <option value="Card">Credit / Debit Card</option>
              <option value="Bank Transfer">Bank Transfer / NEFT</option>
              <option value="Cheque">Cheque / DD</option>
            </select>
          </div>
          <div>
            <label class="tp-label" id="labelFirstPaymentRef">Transaction / Ref No. <span id="refRequiredMark" style="color: #ef4444;">*</span></label>
            <input type="text" name="first_payment_reference" id="first_payment_reference" class="form-control tp-input" placeholder="Ref / UTR / Cheque No.">
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 14px; margin-top: 14px;">
          <div>
            <label class="tp-label">Payment Proof (Optional Screenshot / Slip)</label>
            <input type="file" name="first_payment_proof" id="first_payment_proof" class="form-control tp-input" accept="image/*,application/pdf">
            <span style="font-size: 0.72rem; color: var(--tp-text-muted); display: block; margin-top: 3px;">
              Upload slip or UPI screenshot if available.
            </span>
          </div>
          <div>
            <label class="tp-label">Remarks / Notes</label>
            <input type="text" name="first_payment_notes" id="first_payment_notes" class="form-control tp-input" placeholder="e.g. Initial token payment paid via GPay">
          </div>
        </div>
      </div>
'''

target_marker = '      <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px;">'
if target_marker in html:
    html = html.replace(target_marker, section_first_payment + '\n' + target_marker, 1)
    print("Inserted first payment section into enrollment_form.html!")
else:
    print("ERROR: target_marker not found in enrollment_form.html")

# 3. Add JS validation
js_validation = '''
  // Dynamic First Payment mode & reference validation
  const paymentMethodSelect = document.getElementById('first_payment_method');
  const paymentRefInput = document.getElementById('first_payment_reference');
  const refRequiredMark = document.getElementById('refRequiredMark');
  const firstAmtInput = document.getElementById('first_payment_amount');

  function updateRefRequirement() {
    if (!paymentMethodSelect || !refRequiredMark) return;
    const mode = paymentMethodSelect.value;
    const isCash = (mode === 'Cash');
    if (isCash) {
      refRequiredMark.style.display = 'none';
    } else {
      refRequiredMark.style.display = 'inline';
    }
  }

  if (paymentMethodSelect) {
    paymentMethodSelect.addEventListener('change', updateRefRequirement);
    updateRefRequirement();
  }

  // Pre-submission validation
  const form = document.getElementById('enrollmentForm');
  if (form) {
    form.addEventListener('submit', function(e) {
      if (firstAmtInput && firstAmtInput.value.trim()) {
        const val = parseFloat(firstAmtInput.value.trim());
        if (isNaN(val) || val <= 0) {
          alert('First payment amount must be greater than zero.');
          firstAmtInput.focus();
          e.preventDefault();
          return false;
        }

        const totalPayableText = document.getElementById('previewTotal') ? document.getElementById('previewTotal').textContent.replace(/[^0-9.]/g, '') : '0';
        const totalPayable = parseFloat(totalPayableText) || 0;
        if (totalPayable > 0 && val > totalPayable) {
          alert(`First payment amount (₹${val.toFixed(2)}) cannot exceed the total payable fee (₹${totalPayable.toFixed(2)}).`);
          firstAmtInput.focus();
          e.preventDefault();
          return false;
        }

        const mode = paymentMethodSelect ? paymentMethodSelect.value : 'UPI';
        if (mode !== 'Cash' && paymentRefInput && !paymentRefInput.value.trim()) {
          alert(`Transaction / Reference number is required for payment mode '${mode}'.`);
          paymentRefInput.focus();
          e.preventDefault();
          return false;
        }
      }
    });
  }
'''

target_js_marker = '  // Initial calculation on load\n  recalculateGST();'
if target_js_marker in html:
    html = html.replace(target_js_marker, js_validation + '\n  // Initial calculation on load\n  recalculateGST();', 1)
    print("Inserted JS validation into enrollment_form.html!")
else:
    print("Warning: target_js_marker not found, appending before end of DOMContentLoaded...")
    html = html.replace('  recalculateGST();\n  togglePaymentPlan();', js_validation + '\n  recalculateGST();\n  togglePaymentPlan();', 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated enrollment_form.html successfully!")
