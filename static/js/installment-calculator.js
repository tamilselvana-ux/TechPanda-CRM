/**
 * iTechPanda CRM - Dynamic Installment Auto-Balancing Slider Engine
 * Provides counselors real-time slider controls to adjust down payments & installments
 * with zero rounding errors, auto-absorbing remainders down to the exact rupee.
 */

let currentTotalPayable = 0;
let currentInstallmentSchedule = []; // array of { number, amount, due_date }

function initInstallmentEngine(total, count, startDateStr) {
  currentTotalPayable = Math.round(Number(total) * 100) / 100;
  const numCount = parseInt(count) || 2;
  const baseDate = startDateStr ? new Date(startDateStr) : new Date();

  // Equal initial distribution
  const equalAmt = Math.round((currentTotalPayable / numCount) * 100) / 100;
  const baseSum = Math.round(equalAmt * numCount * 100) / 100;
  const diff = Math.round((currentTotalPayable - baseSum) * 100) / 100;

  currentInstallmentSchedule = [];
  for (let i = 1; i <= numCount; i++) {
    let amt = equalAmt;
    if (i === numCount) {
      amt = Math.round((amt + diff) * 100) / 100;
    }
    const d = new Date(baseDate);
    d.setDate(d.getDate() + (i - 1) * 30);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');

    currentInstallmentSchedule.push({
      number: i,
      amount: Math.max(1, amt),
      due_date: `${yyyy}-${mm}-${dd}`
    });
  }

  renderDynamicInstallmentMatrix();
}

function renderDynamicInstallmentMatrix() {
  const container = document.getElementById('installmentCardsContainer');
  const methodInput = document.getElementById('id_installment_method');
  if (methodInput) methodInput.value = 'MANUAL';
  if (!container) return;

  const scheduledSum = currentInstallmentSchedule.reduce((acc, x) => acc + Number(x.amount || 0), 0);
  const roundedSum = Math.round(scheduledSum * 100) / 100;
  const diff = Math.round((currentTotalPayable - roundedSum) * 100) / 100;

  const totalSpan = document.getElementById('previewScheduledTotal');
  if (totalSpan) {
    if (Math.abs(diff) < 0.01) {
      totalSpan.innerHTML = `<span style="color: #059669; font-weight: 700;">✅ ₹${currentTotalPayable.toLocaleString('en-IN', {minimumFractionDigits: 2})} (Exactly Balanced)</span>`;
    } else if (diff > 0) {
      totalSpan.innerHTML = `<span style="color: #d97706; font-weight: 700;">⚠️ ₹${roundedSum.toLocaleString('en-IN', {minimumFractionDigits: 2})} (₹${diff.toFixed(2)} Remaining)</span>`;
    } else {
      totalSpan.innerHTML = `<span style="color: #dc2626; font-weight: 700;">🚨 ₹${roundedSum.toLocaleString('en-IN', {minimumFractionDigits: 2})} (Exceeds by ₹${Math.abs(diff).toFixed(2)})</span>`;
    }
  }

  container.innerHTML = currentInstallmentSchedule.map((inst, idx) => {
    const isLast = (idx === currentInstallmentSchedule.length - 1);
    const maxVal = Math.max(currentTotalPayable, 1000);
    return `
      <div class="inst-balancer-card" style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <strong style="font-size: 0.82rem; color: #1e293b; text-transform: uppercase;">
            ${idx === 0 ? 'Down Payment / #1' : `Installment #${inst.number}`}
          </strong>
          ${isLast ? '<span class="badge" style="background: #eff6ff; color: #1d4ed8; font-size: 0.68rem; padding: 2px 6px;">Auto-Balancing</span>' : ''}
        </div>

        <div style="margin-bottom: 8px;">
          <label style="font-size: 0.72rem; color: #64748b; display: block; margin-bottom: 2px;">Amount (₹)</label>
          <div style="position: relative;">
            <span style="position: absolute; left: 8px; top: 6px; font-weight: 700; color: #64748b; font-size: 0.85rem;">₹</span>
            <input type="number" step="1" name="manual_amount[]" class="form-control tp-input inst-amount-input" 
                   value="${Math.round(inst.amount)}" min="1" max="${maxVal}"
                   style="padding-left: 22px; font-weight: 700; font-size: 0.95rem; color: #0f172a;"
                   oninput="onInstallmentAmountChange(${idx}, this.value)">
          </div>
        </div>

        <!-- Interactive Range Slider -->
        <div style="margin-bottom: 8px;">
          <input type="range" min="500" max="${maxVal}" step="500" value="${Math.round(inst.amount)}" 
                 style="width: 100%; cursor: pointer;"
                 oninput="onInstallmentSliderChange(${idx}, this.value)">
        </div>

        <div>
          <label style="font-size: 0.72rem; color: #64748b; display: block; margin-bottom: 2px;">Due Date</label>
          <input type="date" name="manual_date[]" class="form-control tp-input" 
                 value="${inst.due_date}" required style="font-size: 0.78rem; padding: 4px 8px;"
                 onchange="onInstallmentDateChange(${idx}, this.value)">
        </div>
      </div>
    `;
  }).join('');
}

function onInstallmentAmountChange(index, newAmtVal) {
  let val = Math.round(Number(newAmtVal) || 0);
  if (val < 0) val = 0;
  currentInstallmentSchedule[index].amount = val;

  // Auto-sync first installment with first payment field if paying today
  if (index === 0) {
    const firstPayInput = document.getElementById('id_first_payment_amount');
    if (firstPayInput && (!firstPayInput.value || Number(firstPayInput.value) > 0)) {
      firstPayInput.value = val;
    }
  }

  // Auto-balance remaining installments
  autoBalanceRemaining(index);
  renderDynamicInstallmentMatrix();
}

function onInstallmentSliderChange(index, sliderVal) {
  onInstallmentAmountChange(index, sliderVal);
}

function onInstallmentDateChange(index, newDateVal) {
  if (currentInstallmentSchedule[index]) {
    currentInstallmentSchedule[index].due_date = newDateVal;
  }
}

function autoBalanceRemaining(changedIndex) {
  const n = currentInstallmentSchedule.length;
  if (n <= 1) return;

  // If the last installment was changed, adjust the second-to-last or previous
  let targetIndex = n - 1;
  if (changedIndex === n - 1) {
    targetIndex = n - 2;
  }

  let sumOthers = 0;
  for (let i = 0; i < n; i++) {
    if (i !== targetIndex) {
      sumOthers += Number(currentInstallmentSchedule[i].amount || 0);
    }
  }

  const remainder = Math.round((currentTotalPayable - sumOthers) * 100) / 100;
  if (remainder >= 0) {
    currentInstallmentSchedule[targetIndex].amount = remainder;
  }
}

function equalizeAllInstallments() {
  const countSelect = document.getElementById('id_installment_count');
  const count = countSelect ? countSelect.value : currentInstallmentSchedule.length;
  const firstDate = document.getElementById('id_first_date') ? document.getElementById('id_first_date').value : '';
  initInstallmentEngine(currentTotalPayable, count, firstDate);
}
