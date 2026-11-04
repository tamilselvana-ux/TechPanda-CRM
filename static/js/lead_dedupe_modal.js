/**
 * lead_dedupe_modal.js
 * Intelligent real-time duplicate lead detector and interactive warning modal.
 * Provides 3 distinct operational paths: Open / Merge / Create Anyway.
 */
document.addEventListener('DOMContentLoaded', function () {
  const phoneInput = document.getElementById('id_phone');
  const emailInput = document.getElementById('id_email');
  const nameInput = document.getElementById('id_name');
  const form = document.querySelector('form[method="POST"]') || document.querySelector('form');

  if (!phoneInput || !form) return;

  const liveAlert = document.getElementById('tpDedupeLiveAlert');
  const dedupeIdSpan = document.getElementById('tpDedupeId');
  const dedupeDetailsSpan = document.getElementById('tpDedupeDetails');
  const dedupeOpenLink = document.getElementById('tpDedupeOpenLink');

  const modalEl = document.getElementById('tpDedupePromptModal');
  const modalLeadCard = document.getElementById('tpModalLeadCard');
  const modalBtnOpen = document.getElementById('tpModalBtnOpen');
  const modalBtnMerge = document.getElementById('tpModalBtnMerge');
  const modalBtnForce = document.getElementById('tpModalBtnForce');

  let activeCandidate = null;
  let debounceTimer = null;
  let isOverrideConfirmed = false;

  // Insert live alert right beneath the phone input if not already placed
  if (liveAlert && phoneInput.parentNode) {
    phoneInput.parentNode.appendChild(liveAlert);
  }

  function checkDuplicates() {
    const phone = phoneInput ? phoneInput.value.trim() : '';
    const email = emailInput ? emailInput.value.trim() : '';
    const name = nameInput ? nameInput.value.trim() : '';

    // Only query if phone has >= 6 digits or email contains @
    const digits = phone.replace(/\D/g, '');
    if (digits.length < 6 && (!email || !email.includes('@'))) {
      if (liveAlert) liveAlert.style.display = 'none';
      activeCandidate = null;
      return;
    }

    const params = new URLSearchParams();
    if (phone) params.append('phone', phone);
    if (email) params.append('email', email);
    if (name) params.append('name', name);

    fetch('/api/leads/check-duplicate/?' + params.toString(), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(res => res.json())
      .then(data => {
        if (data.has_duplicates && data.duplicates && data.duplicates.length > 0) {
          activeCandidate = data.duplicates[0];
          renderLiveAlert(activeCandidate);
        } else {
          activeCandidate = null;
          if (liveAlert) liveAlert.style.display = 'none';
        }
      })
      .catch(err => {
        console.warn('Duplicate check non-blocking error:', err);
      });
  }

  function renderLiveAlert(candidate) {
    if (!liveAlert) return;
    if (dedupeIdSpan) dedupeIdSpan.textContent = candidate.id;
    if (dedupeDetailsSpan) {
      dedupeDetailsSpan.textContent = `(${candidate.name} · ${candidate.phone} · ${candidate.status})`;
    }
    if (dedupeOpenLink) {
      dedupeOpenLink.href = candidate.detail_url;
    }
    liveAlert.style.display = 'block';
  }

  function triggerDebouncedCheck() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(checkDuplicates, 350);
  }

  if (phoneInput) {
    phoneInput.addEventListener('input', triggerDebouncedCheck);
    phoneInput.addEventListener('blur', checkDuplicates);
  }
  if (emailInput) {
    emailInput.addEventListener('input', triggerDebouncedCheck);
    emailInput.addEventListener('blur', checkDuplicates);
  }
  if (nameInput) {
    nameInput.addEventListener('blur', checkDuplicates);
  }

  // Handle Form Submission Interception
  form.addEventListener('submit', function (e) {
    if (isOverrideConfirmed || !activeCandidate) {
      return true; // allow submission
    }

    // A duplicate is present and user hasn't explicitly chosen force or merge
    e.preventDefault();

    // Populate and show the modal
    if (modalLeadCard) {
      modalLeadCard.innerHTML = `
        <div style="font-weight: 800; font-size: 14px; color: #0f172a; margin-bottom: 4px;">
          Lead #${activeCandidate.id}: ${activeCandidate.name}
        </div>
        <div style="color: #64748b; font-size: 12.5px; margin-bottom: 8px;">
          📞 ${activeCandidate.phone} &nbsp;|&nbsp; ✉️ ${activeCandidate.email || 'N/A'}
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px;">
          <span style="background: #e2e8f0; color: #334155; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 700;">📍 ${activeCandidate.branch_name}</span>
          <span style="background: #dbeafe; color: #1e40af; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 700;">🏷️ ${activeCandidate.status}</span>
          <span style="background: #f1f5f9; color: #475569; padding: 2px 7px; border-radius: 4px; font-size: 11px;">👤 ${activeCandidate.assigned_to}</span>
        </div>
        <div style="font-size: 12px; color: #b45309; font-weight: 600;">
          Match Reason: ${activeCandidate.reason}
        </div>
      `;
    }

    if (modalBtnOpen) {
      modalBtnOpen.href = activeCandidate.detail_url;
    }

    // Modal action: Merge
    if (modalBtnMerge) {
      modalBtnMerge.onclick = function () {
        let actionInput = form.querySelector('input[name="action"]');
        if (!actionInput) {
          actionInput = document.createElement('input');
          actionInput.type = 'hidden';
          actionInput.name = 'action';
          form.appendChild(actionInput);
        }
        actionInput.value = 'merge';

        let targetInput = form.querySelector('input[name="merge_target_id"]');
        if (!targetInput) {
          targetInput = document.createElement('input');
          targetInput.type = 'hidden';
          targetInput.name = 'merge_target_id';
          form.appendChild(targetInput);
        }
        targetInput.value = activeCandidate.id;

        isOverrideConfirmed = true;
        form.submit();
      };
    }

    // Modal action: Create Anyway (Force)
    if (modalBtnForce) {
      modalBtnForce.onclick = function () {
        let forceInput = form.querySelector('input[name="force_create"]');
        if (!forceInput) {
          forceInput = document.createElement('input');
          forceInput.type = 'hidden';
          forceInput.name = 'force_create';
          form.appendChild(forceInput);
        }
        forceInput.value = '1';

        isOverrideConfirmed = true;
        form.submit();
      };
    }

    // Open bootstrap modal if available, otherwise native fallback
    if (window.bootstrap && bootstrap.Modal) {
      const bsModal = new bootstrap.Modal(modalEl);
      bsModal.show();
    } else {
      modalEl.style.display = 'block';
      modalEl.classList.add('show');
    }
  });
});
