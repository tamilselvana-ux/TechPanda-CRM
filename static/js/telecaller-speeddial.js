/**
 * iTechPanda CRM - 1-Click Telecaller Speed-Dial Keyboard Dispositions (Item 142)
 * Enables lightning-fast call logging via hotkeys 1-5 without touching the mouse.
 */
(function() {
  'use strict';

  function applyQuickDisposition(hotkey) {
    var form = document.getElementById('call-notes-completion-form');
    if (!form) return;

    var modal = document.getElementById('lead-details-modal') || document.querySelector('.lead-details-modal-wrap');
    var isModalVisible = modal && (modal.style.display !== 'none' && !modal.classList.contains('hidden'));
    var lockModal = document.getElementById('call-notes-required-modal');
    var isLockVisible = lockModal && lockModal.style.display !== 'none';

    if (!isModalVisible && !isLockVisible) return;

    var notesArea = document.getElementById('call-form-notes');
    var outcomeSelect = document.getElementById('call-form-outcome');
    var statusSelect = document.getElementById('call-form-lead-status');
    var followupDate = document.getElementById('call-form-followup-date');
    var followupTime = document.getElementById('call-form-followup-time');

    if (!outcomeSelect) return;

    var outcome = 'Follow-up Required';
    var note = '';
    var status = 'Follow-up';

    if (hotkey === '1') {
      outcome = 'RNR';
      note = 'RNR - Ring No Response (Unanswered call)';
      status = 'Follow-up';
    } else if (hotkey === '2') {
      outcome = 'Busy';
      note = 'Line Busy - Customer engaged on another call';
      status = 'Follow-up';
    } else if (hotkey === '3') {
      outcome = 'Callback Requested';
      note = 'Callback requested in 2 hours';
      status = 'Follow-up';
      // Set follow-up date and time 2 hours from now
      var now = new Date();
      now.setHours(now.getHours() + 2);
      if (followupDate) followupDate.value = now.toISOString().split('T')[0];
      if (followupTime) followupTime.value = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
    } else if (hotkey === '4') {
      outcome = 'Not Interested';
      note = 'Student stated not interested in admission';
      status = 'Not Interested';
    } else if (hotkey === '5') {
      outcome = 'Interested';
      note = 'Hot prospect! Student interested, requested syllabus and fee structure';
      status = 'Interested';
    } else {
      return;
    }

    // Set values
    outcomeSelect.value = outcome;
    if (notesArea) notesArea.value = note;
    if (statusSelect && status) statusSelect.value = status;

    // Visual feedback
    var btn = document.querySelector('.tp-quick-btn[data-hotkey="' + hotkey + '"]');
    if (btn) {
      btn.style.transform = 'scale(0.95)';
      setTimeout(function() { btn.style.transform = ''; }, 150);
    }

    // Auto submit form
    var saveBtn = document.getElementById('save-call-notes-btn');
    if (saveBtn) {
      saveBtn.click();
    } else {
      form.submit();
    }
  }

  // Keyboard shortcut listener
  document.addEventListener('keydown', function(e) {
    // If user is actively typing in textarea or input, do not hijack number keys
    var tag = e.target.tagName.toLowerCase();
    if (tag === 'textarea' || (tag === 'input' && e.target.type !== 'button' && e.target.type !== 'submit')) {
      return;
    }

    if (e.key >= '1' && e.key <= '5') {
      var modal = document.getElementById('lead-details-modal') || document.querySelector('.lead-details-modal-wrap');
      var isModalVisible = modal && (modal.style.display !== 'none' && !modal.classList.contains('hidden'));
      var lockModal = document.getElementById('call-notes-required-modal');
      var isLockVisible = lockModal && lockModal.style.display !== 'none';

      if (isModalVisible || isLockVisible) {
        e.preventDefault();
        applyQuickDisposition(e.key);
      }
    }
  });

  // Attach button click listeners
  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.tp-quick-btn').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        var key = btn.getAttribute('data-hotkey');
        if (key) applyQuickDisposition(key);
      });
    });
  });
})();
