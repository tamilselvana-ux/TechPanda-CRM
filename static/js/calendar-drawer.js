/**
 * iTechPanda CRM — Universal Responsive Calendar Drawer Controller
 * Singleton controller managing right-side slide-over (desktop >= 900px)
 * and mobile bottom sheet (< 600px) across all 17 CRM date-filtered views.
 */
(function () {
  'use strict';

  // Date Formatting Helpers (Local Timezone: Asia/Kolkata)
  function formatYMD(d) {
    if (!d || isNaN(d.getTime())) return '';
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var day = String(d.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + day;
  }

  function formatHumanDate(d) {
    if (!d || isNaN(d.getTime())) return '';
    var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return String(d.getDate()).padStart(2, '0') + ' ' + months[d.getMonth()] + ' ' + d.getFullYear();
  }

  function parseYMD(str) {
    if (!str || typeof str !== 'string') return null;
    var parts = str.trim().split('-');
    if (parts.length !== 3) return null;
    var y = parseInt(parts[0], 10);
    var m = parseInt(parts[1], 10) - 1;
    var d = parseInt(parts[2], 10);
    var dt = new Date(y, m, d);
    return isNaN(dt.getTime()) ? null : dt;
  }

  function isSameDay(d1, d2) {
    if (!d1 || !d2) return false;
    return d1.getFullYear() === d2.getFullYear() &&
           d1.getMonth() === d2.getMonth() &&
           d1.getDate() === d2.getDate();
  }

  function isBetween(d, start, end) {
    if (!d || !start || !end) return false;
    var time = d.getTime();
    var s = new Date(start.getFullYear(), start.getMonth(), start.getDate()).getTime();
    var e = new Date(end.getFullYear(), end.getMonth(), end.getDate()).getTime();
    return time > s && time < e;
  }

  // Presets Definition
  function getPresetRange(presetId) {
    var today = new Date();
    today.setHours(0, 0, 0, 0);

    if (presetId === 'today') {
      return { start: today, end: today };
    }
    if (presetId === 'yesterday') {
      var yest = new Date(today);
      yest.setDate(today.getDate() - 1);
      return { start: yest, end: yest };
    }
    if (presetId === 'last_7_days') {
      var l7 = new Date(today);
      l7.setDate(today.getDate() - 6);
      return { start: l7, end: today };
    }
    if (presetId === 'last_30_days') {
      var l30 = new Date(today);
      l30.setDate(today.getDate() - 29);
      return { start: l30, end: today };
    }
    if (presetId === 'this_month') {
      var tmStart = new Date(today.getFullYear(), today.getMonth(), 1);
      return { start: tmStart, end: today };
    }
    if (presetId === 'last_month') {
      var lmStart = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      var lmEnd = new Date(today.getFullYear(), today.getMonth(), 0);
      return { start: lmStart, end: lmEnd };
    }
    if (presetId === 'this_fy') {
      var curMonth = today.getMonth(); // 0-indexed (3 is April)
      var fyYear = curMonth >= 3 ? today.getFullYear() : today.getFullYear() - 1;
      var fyStart = new Date(fyYear, 3, 1); // April 1
      return { start: fyStart, end: today };
    }
    return { start: null, end: null };
  }

  // Calendar Drawer Core Singleton
  var CalendarDrawer = {
    isOpen: false,
    activeTrigger: null,
    activeForm: null,
    inputs: {
      start: null,
      end: null,
      period: null
    },
    state: {
      start: null,
      end: null,
      hover: null,
      preset: null,
      viewMonth: new Date() // First displayed month
    },
    dom: {},

    init: function () {
      this.dom.backdrop = document.getElementById('calendar-drawer-backdrop');
      this.dom.drawer = document.getElementById('calendar-drawer');
      if (!this.dom.drawer) return;

      this.dom.closeBtn = document.getElementById('cd-close-btn');
      this.dom.clearBtn = document.getElementById('cd-clear-btn');
      this.dom.cancelBtn = document.getElementById('cd-cancel-btn');
      this.dom.applyBtn = document.getElementById('cd-apply-btn');
      this.dom.startInput = document.getElementById('cd-start-input');
      this.dom.endInput = document.getElementById('cd-end-input');
      this.dom.errorAlert = document.getElementById('cd-error-alert');
      this.dom.errorText = document.getElementById('cd-error-text');
      this.dom.activeRangePill = document.getElementById('cd-active-range-pill');
      this.dom.prevMonthBtn = document.getElementById('cd-prev-month');
      this.dom.nextMonthBtn = document.getElementById('cd-next-month');
      this.dom.monthHeaders = document.getElementById('cd-month-headers');
      this.dom.monthsContainer = document.getElementById('cd-months-container');

      this.bindEvents();
      this.mountSmartDateContainers();
      this.scanAndBindTriggers();
    },

    bindEvents: function () {
      var self = this;

      // Backdrop & Close
      if (this.dom.backdrop) {
        this.dom.backdrop.addEventListener('click', function () { self.close(); });
      }
      if (this.dom.closeBtn) {
        this.dom.closeBtn.addEventListener('click', function () { self.close(); });
      }
      if (this.dom.cancelBtn) {
        this.dom.cancelBtn.addEventListener('click', function () { self.close(); });
      }

      // Clear & Apply
      if (this.dom.clearBtn) {
        this.dom.clearBtn.addEventListener('click', function () { self.clearAndSubmit(); });
      }
      if (this.dom.applyBtn) {
        this.dom.applyBtn.addEventListener('click', function () { self.applyAndSubmit(); });
      }

      // Presets
      var presetButtons = this.dom.drawer.querySelectorAll('.cd-preset-pill');
      presetButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
          var presetId = btn.getAttribute('data-preset');
          self.selectPreset(presetId);
        });
      });

      // Manual Inputs
      if (this.dom.startInput) {
        this.dom.startInput.addEventListener('change', function () {
          var dt = parseYMD(self.dom.startInput.value);
          self.state.start = dt;
          self.state.preset = 'custom';
          self.validateAndUpdateUI();
          self.renderCalendar();
        });
      }
      if (this.dom.endInput) {
        this.dom.endInput.addEventListener('change', function () {
          var dt = parseYMD(self.dom.endInput.value);
          self.state.end = dt;
          self.state.preset = 'custom';
          self.validateAndUpdateUI();
          self.renderCalendar();
        });
      }

      // Month Navigation
      if (this.dom.prevMonthBtn) {
        this.dom.prevMonthBtn.addEventListener('click', function () {
          self.state.viewMonth = new Date(self.state.viewMonth.getFullYear(), self.state.viewMonth.getMonth() - 1, 1);
          self.renderCalendar();
        });
      }
      if (this.dom.nextMonthBtn) {
        this.dom.nextMonthBtn.addEventListener('click', function () {
          self.state.viewMonth = new Date(self.state.viewMonth.getFullYear(), self.state.viewMonth.getMonth() + 1, 1);
          self.renderCalendar();
        });
      }

      // Global Keyboard Trap & Escape
      document.addEventListener('keydown', function (e) {
        if (!self.isOpen) return;
        if (e.key === 'Escape') {
          e.preventDefault();
          self.close();
        }
      });

      // Window Resize Handler (Re-render 1 vs 2 months adaptively)
      var resizeTimeout;
      window.addEventListener('resize', function () {
        if (!self.isOpen) return;
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function () {
          self.renderCalendar();
        }, 120);
      });
    },

    mountSmartDateContainers: function () {
      var containers = document.querySelectorAll('.tp-smart-date-container');
      containers.forEach(function (container) {
        // If container already has a trigger button, skip creation
        if (container.querySelector('.calendar-drawer-trigger, .tp-smart-date-trigger')) return;

        var startInput = container.querySelector('input[name="start_date"], input[name="date_from"], input[name="from_date"], input[name="from"]');
        var endInput = container.querySelector('input[name="end_date"], input[name="date_to"], input[name="to_date"], input[name="to"]');

        var startVal = startInput ? startInput.value : '';
        var endVal = endInput ? endInput.value : '';

        var sDate = parseYMD(startVal);
        var eDate = parseYMD(endVal);

        var hasActive = !!(sDate || eDate);
        var displayLabel = 'Select Date Range';
        if (sDate && eDate) {
          displayLabel = formatHumanDate(sDate) + ' – ' + formatHumanDate(eDate);
        } else if (sDate) {
          displayLabel = 'From ' + formatHumanDate(sDate);
        }

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'calendar-drawer-trigger tp-smart-date-trigger' + (container.classList.contains('compact') ? ' compact' : '') + (container.classList.contains('w-100') ? ' w-100' : '');
        btn.setAttribute('aria-haspopup', 'dialog');
        btn.setAttribute('title', 'Open Responsive Calendar Drawer');

        var calIconSvg = '<svg class="tp-smart-date-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>';
        var chevronSvg = '<svg class="tp-smart-date-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"></polyline></svg>';

        var leftWrap = document.createElement('div');
        leftWrap.style.display = 'inline-flex';
        leftWrap.style.alignItems = 'center';
        leftWrap.style.gap = '8px';
        leftWrap.style.overflow = 'hidden';
        leftWrap.innerHTML = calIconSvg;

        var labelSpan = document.createElement('span');
        labelSpan.className = 'tp-smart-date-label range-label';
        labelSpan.textContent = displayLabel;
        leftWrap.appendChild(labelSpan);

        if (hasActive) {
          var dot = document.createElement('span');
          dot.className = 'tp-smart-date-dot active';
          leftWrap.appendChild(dot);
        }

        var rightWrap = document.createElement('div');
        rightWrap.style.display = 'inline-flex';
        rightWrap.style.alignItems = 'center';
        rightWrap.style.gap = '4px';

        if (hasActive) {
          var quickReset = document.createElement('span');
          quickReset.className = 'tp-smart-date-quick-reset';
          quickReset.setAttribute('title', 'Clear date filter');
          quickReset.innerHTML = '&times;';
          quickReset.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            if (startInput) startInput.value = '';
            if (endInput) endInput.value = '';
            var form = container.closest('form');
            if (form) {
              var pInput = form.querySelector('input[name="page"]');
              if (pInput) pInput.value = '1';
              form.submit();
            }
          });
          rightWrap.appendChild(quickReset);
        }

        rightWrap.insertAdjacentHTML('beforeend', chevronSvg);

        btn.appendChild(leftWrap);
        btn.appendChild(rightWrap);
        container.appendChild(btn);
      });
    },

    scanAndBindTriggers: function () {
      var self = this;
      var triggers = document.querySelectorAll(
        '.calendar-drawer-trigger, [data-calendar-drawer], .tp-date-range-badge, .smart-calendar-container, #customRangeToggleBtn'
      );

      triggers.forEach(function (trigger) {
        if (trigger._calendarDrawerBound) return;
        trigger._calendarDrawerBound = true;
        trigger.style.cursor = 'pointer';

        trigger.addEventListener('click', function (e) {
          if (e.target.classList.contains('tp-smart-date-quick-reset')) return;
          e.preventDefault();
          e.stopPropagation();
          self.open(trigger);
        });
      });
    },

    open: function (triggerEl) {
      this.activeTrigger = triggerEl;
      this.activeForm = triggerEl.closest('form') || document.querySelector('form.filter-form, form.date-filter-form, form#filter-form, form');

      this.resolveFormInputs(triggerEl);
      this.loadInitialState();

      // Open drawer in DOM
      document.body.classList.add('cd-drawer-open');
      this.dom.drawer.setAttribute('aria-hidden', 'false');
      this.dom.drawer.removeAttribute('tabindex');
      this.isOpen = true;

      this.renderCalendar();
      this.validateAndUpdateUI();

      // Accessibility: focus first preset
      var firstPill = this.dom.drawer.querySelector('.cd-preset-pill.active') || this.dom.drawer.querySelector('.cd-preset-pill');
      if (firstPill) firstPill.focus();
    },

    close: function () {
      if (!this.isOpen) return;
      document.body.classList.remove('cd-drawer-open');
      this.dom.drawer.setAttribute('aria-hidden', 'true');
      this.dom.drawer.setAttribute('tabindex', '-1');
      this.isOpen = false;

      // Return focus to trigger
      if (this.activeTrigger && typeof this.activeTrigger.focus === 'function') {
        this.activeTrigger.focus();
      }
    },

    resolveFormInputs: function (triggerEl) {
      var root = triggerEl.closest('form') || triggerEl.closest('.filter-card') || triggerEl.parentElement;

      // Start date input candidates
      this.inputs.start = root.querySelector('input[name="start_date"], input[name="date_from"], input[name="from_date"], input[name="from"]');
      // End date input candidates
      this.inputs.end = root.querySelector('input[name="end_date"], input[name="date_to"], input[name="to_date"], input[name="to"]');
      // Period candidate
      this.inputs.period = root.querySelector('input[name="period"], select[name="period"]');

      // Fallback: search document if form inputs were not within direct root
      if (!this.inputs.start) {
        this.inputs.start = document.querySelector('input[name="start_date"], input[name="date_from"], input[name="from_date"], input[name="from"]');
      }
      if (!this.inputs.end) {
        this.inputs.end = document.querySelector('input[name="end_date"], input[name="date_to"], input[name="to_date"], input[name="to"]');
      }
      if (!this.inputs.period) {
        this.inputs.period = document.querySelector('input[name="period"], select[name="period"]');
      }
    },

    loadInitialState: function () {
      var startVal = this.inputs.start ? this.inputs.start.value : '';
      var endVal = this.inputs.end ? this.inputs.end.value : '';
      var periodVal = this.inputs.period ? this.inputs.period.value : '';

      this.state.start = parseYMD(startVal);
      this.state.end = parseYMD(endVal);
      this.state.preset = periodVal || (this.state.start ? 'custom' : 'this_month');
      this.state.hover = null;

      if (this.state.start) {
        this.state.viewMonth = new Date(this.state.start.getFullYear(), this.state.start.getMonth(), 1);
      } else {
        var now = new Date();
        this.state.viewMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      }
    },

    selectPreset: function (presetId) {
      this.state.preset = presetId;
      if (presetId === 'custom') {
        // Keeps current dates
      } else {
        var range = getPresetRange(presetId);
        this.state.start = range.start;
        this.state.end = range.end;
        if (range.start) {
          this.state.viewMonth = new Date(range.start.getFullYear(), range.start.getMonth(), 1);
        }
      }
      this.validateAndUpdateUI();
      this.renderCalendar();
    },

    validateAndUpdateUI: function () {
      var start = this.state.start;
      var end = this.state.end;

      if (this.dom.startInput) this.dom.startInput.value = formatYMD(start);
      if (this.dom.endInput) this.dom.endInput.value = formatYMD(end);

      var isValid = true;
      var errorMsg = '';

      if (start && end && start.getTime() > end.getTime()) {
        isValid = false;
        errorMsg = 'Start date cannot be after End date.';
      }

      if (!isValid) {
        this.dom.errorAlert.style.display = 'flex';
        this.dom.errorText.textContent = errorMsg;
        this.dom.applyBtn.disabled = true;
      } else {
        this.dom.errorAlert.style.display = 'none';
        this.dom.applyBtn.disabled = false;
      }

      // Update preset pills active state
      var pills = this.dom.drawer.querySelectorAll('.cd-preset-pill');
      var currentPreset = this.state.preset || 'custom';
      pills.forEach(function (pill) {
        if (pill.getAttribute('data-preset') === currentPreset) {
          pill.classList.add('active');
        } else {
          pill.classList.remove('active');
        }
      });

      // Update header active range pill
      if (start && end) {
        this.dom.activeRangePill.textContent = formatHumanDate(start) + ' – ' + formatHumanDate(end);
      } else if (start) {
        this.dom.activeRangePill.textContent = 'From ' + formatHumanDate(start);
      } else {
        this.dom.activeRangePill.textContent = 'All Time';
      }
    },

    renderCalendar: function () {
      var container = this.dom.monthsContainer;
      var headersRow = this.dom.monthHeaders;
      if (!container || !headersRow) return;

      container.innerHTML = '';
      headersRow.innerHTML = '';

      var isMobile = window.innerWidth <= 600;
      var numMonths = isMobile ? 1 : 2;

      var monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
      var weekdays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

      var baseMonth = new Date(this.state.viewMonth.getFullYear(), this.state.viewMonth.getMonth(), 1);

      for (var mIdx = 0; mIdx < numMonths; mIdx++) {
        var currentMonth = new Date(baseMonth.getFullYear(), baseMonth.getMonth() + mIdx, 1);
        var year = currentMonth.getFullYear();
        var month = currentMonth.getMonth();

        // 1. Header Title
        var titleEl = document.createElement('div');
        titleEl.className = 'cd-month-title';
        titleEl.textContent = monthNames[month] + ' ' + year;
        headersRow.appendChild(titleEl);

        // 2. Month Card
        var monthCard = document.createElement('div');
        monthCard.className = 'cd-month-card';

        // Weekdays Header
        var weekdaysRow = document.createElement('div');
        weekdaysRow.className = 'cd-weekdays';
        weekdays.forEach(function (wd) {
          var span = document.createElement('span');
          span.className = 'cd-weekday';
          span.textContent = wd;
          weekdaysRow.appendChild(span);
        });
        monthCard.appendChild(weekdaysRow);

        // Days Grid
        var matrix = document.createElement('div');
        matrix.className = 'cd-days-matrix';

        var firstDayOfWeek = new Date(year, month, 1).getDay(); // 0 = Sun
        var daysInMonth = new Date(year, month + 1, 0).getDate();
        var prevMonthDays = new Date(year, month, 0).getDate();

        var today = new Date();
        today.setHours(0, 0, 0, 0);

        // Leading padding days from previous month
        for (var p = firstDayOfWeek - 1; p >= 0; p--) {
          var padCell = document.createElement('span');
          padCell.className = 'cd-day-cell cd-day-pad';
          padCell.textContent = String(prevMonthDays - p);
          matrix.appendChild(padCell);
        }

        // Active days in this month
        for (var dayNum = 1; dayNum <= daysInMonth; dayNum++) {
          var cellDate = new Date(year, month, dayNum);
          var btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'cd-day-cell';
          btn.textContent = String(dayNum);
          btn.setAttribute('data-date', formatYMD(cellDate));
          btn.setAttribute('aria-label', formatHumanDate(cellDate));

          if (isSameDay(cellDate, today)) {
            btn.classList.add('is-today');
          }

          var start = this.state.start;
          var end = this.state.end || this.state.hover;

          if (start && isSameDay(cellDate, start)) {
            btn.classList.add('is-start');
            if (end && isSameDay(cellDate, end)) {
              btn.classList.add('is-end');
            }
          } else if (end && isSameDay(cellDate, end)) {
            btn.classList.add('is-end');
          } else if (start && end && isBetween(cellDate, start < end ? start : end, start < end ? end : start)) {
            btn.classList.add('is-in-range');
          }

          this.bindDayCell(btn, cellDate);
          matrix.appendChild(btn);
        }

        monthCard.appendChild(matrix);
        container.appendChild(monthCard);
      }
    },

    bindDayCell: function (btn, cellDate) {
      var self = this;

      btn.addEventListener('mouseenter', function () {
        if (self.state.start && !self.state.end) {
          self.state.hover = cellDate;
          self.renderCalendar();
        }
      });

      btn.addEventListener('click', function () {
        if (!self.state.start || (self.state.start && self.state.end)) {
          // First click: select start date
          self.state.start = cellDate;
          self.state.end = null;
          self.state.hover = null;
          self.state.preset = 'custom';
        } else {
          // Second click: select end date
          if (cellDate.getTime() < self.state.start.getTime()) {
            self.state.end = self.state.start;
            self.state.start = cellDate;
          } else {
            self.state.end = cellDate;
          }
          self.state.hover = null;
          self.state.preset = 'custom';
        }

        self.validateAndUpdateUI();
        self.renderCalendar();
      });
    },

    applyAndSubmit: function () {
      if (this.dom.applyBtn.disabled) return;

      var startStr = formatYMD(this.state.start);
      var endStr = formatYMD(this.state.end);

      // Write values back to active form inputs
      if (this.inputs.start) {
        this.inputs.start.value = startStr;
        this.inputs.start.dispatchEvent(new Event('change', { bubbles: true }));
      }
      if (this.inputs.end) {
        this.inputs.end.value = endStr;
        this.inputs.end.dispatchEvent(new Event('change', { bubbles: true }));
      }
      if (this.inputs.period) {
        if (this.inputs.period.tagName === 'SELECT') {
          // Check if custom option exists, else set or keep
          var hasCustom = Array.from(this.inputs.period.options).some(function (opt) { return opt.value === 'custom'; });
          if (hasCustom) this.inputs.period.value = 'custom';
        } else {
          this.inputs.period.value = this.state.preset || 'custom';
        }
        this.inputs.period.dispatchEvent(new Event('change', { bubbles: true }));
      }

      // Update trigger label if it has a human readable text container
      if (this.activeTrigger) {
        var labelEl = this.activeTrigger.querySelector('.tp-smart-date-label, .range-label, .tp-date-label, .date-range-text');
        if (labelEl && startStr && endStr) {
          labelEl.textContent = formatHumanDate(this.state.start) + ' – ' + formatHumanDate(this.state.end);
        }
      }

      // Reset pagination to page 1
      if (this.activeForm) {
        var pageInput = this.activeForm.querySelector('input[name="page"]');
        if (pageInput) pageInput.value = '1';
        this.close();
        this.activeForm.submit();
      } else {
        var url = new URL(window.location.href);
        if (this.inputs.start) url.searchParams.set(this.inputs.start.name, startStr);
        if (this.inputs.end) url.searchParams.set(this.inputs.end.name, endStr);
        url.searchParams.delete('page');
        this.close();
        window.location.href = url.toString();
      }
    },

    clearAndSubmit: function () {
      if (this.inputs.start) {
        this.inputs.start.value = '';
        this.inputs.start.dispatchEvent(new Event('change', { bubbles: true }));
      }
      if (this.inputs.end) {
        this.inputs.end.value = '';
        this.inputs.end.dispatchEvent(new Event('change', { bubbles: true }));
      }
      if (this.inputs.period) {
        this.inputs.period.value = '';
        this.inputs.period.dispatchEvent(new Event('change', { bubbles: true }));
      }

      if (this.activeForm) {
        var pageInput = this.activeForm.querySelector('input[name="page"]');
        if (pageInput) pageInput.value = '1';
        this.close();
        this.activeForm.submit();
      } else {
        var url = new URL(window.location.href);
        ['start_date', 'end_date', 'date_from', 'date_to', 'from_date', 'to_date', 'from', 'to', 'period', 'page'].forEach(function(k) {
          url.searchParams.delete(k);
        });
        this.close();
        window.location.href = url.toString();
      }
    }
  };

  // Auto-initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { CalendarDrawer.init(); });
  } else {
    CalendarDrawer.init();
  }

  // Export globally for programmatic control
  window.CalendarDrawer = CalendarDrawer;
})();
