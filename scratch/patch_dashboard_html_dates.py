path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\accountant\dashboard.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add active range badge under header
header_needle = """      <p style="color: var(--tp-text-muted, #64748b); font-size: 0.88rem; margin: 5px 0 0 0;">
        Real-time financial reconciliation, collection auditing, payment verification queues, and branch ledger analytics.
      </p>"""

header_replacement = """      <p style="color: var(--tp-text-muted, #64748b); font-size: 0.88rem; margin: 5px 0 0 0;">
        Real-time financial reconciliation, collection auditing, payment verification queues, and branch ledger analytics.
      </p>
      <div style="display: flex; align-items: center; gap: 10px; margin-top: 8px;">
        <span class="tp-date-range-badge" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.25); color: #3b82f6; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 700;">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
          <span>{{ showing_range_label }}</span>
        </span>
      </div>"""

if header_needle in html:
    html = html.replace(header_needle, header_replacement, 1)
    print("Added showing_range_label badge to dashboard header!")

# 2. Replace Filter Bar Section
filter_section_needle = """  <!-- =================================================================== -->
  <!-- 2. FILTER & AUDIT SCOPE BAR                                         -->
  <!-- =================================================================== -->
  <div class="filter-card tp-card" style="background: var(--tp-surface-card, #ffffff); border-radius: 12px; border: 1px solid var(--tp-surface-border, #e2e8f0); padding: 16px 20px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
    <form method="get" action="" style="display: flex; flex-wrap: wrap; gap: 14px; align-items: flex-end;">
      
      <!-- Date Range Controls (Smart Range Picker & Manual Dates) -->
      <div style="flex: 0 0 auto; min-width: 240px;">
        <label style="display: block; font-size: 0.76rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--tp-text-muted, #64748b); margin-bottom: 5px;">Custom Date Range</label>
        <div class="tp-smart-date-container" style="position: relative;">
          <input type="date" name="start_date" value="{{ start_date }}" style="display: none;">
          <input type="date" name="end_date" value="{{ end_date }}" style="display: none;">
        </div>
      </div>

      {% if branches|length > 1 %}
      <div style="flex: 1 1 180px; min-width: 170px;">
        <label style="display: block; font-size: 0.76rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--tp-text-muted, #64748b); margin-bottom: 5px;">Branch Center</label>
        <select name="branch" class="form-select tp-select" style="font-size: 0.85rem; padding: 7px 10px; border-radius: 8px; border: 1px solid var(--tp-surface-border, #cbd5e1); width: 100%;">
          <option value="">All Accessible Branches</option>
          {% for b in branches %}
          <option value="{{ b.id }}" {% if selected_branch_id == b.id %}selected{% endif %}>{{ b.name }}</option>
          {% endfor %}
        </select>
      </div>
      {% endif %}

      <div style="display: flex; gap: 8px; align-items: center;">
        <button type="submit" class="btn btn-primary tp-btn-primary" style="padding: 7px 16px; font-size: 0.85rem; font-weight: 700; border-radius: 8px;">
          Filter Ledger
        </button>
        <a href="{% url 'accountant_dashboard' %}" class="btn btn-secondary tp-btn-secondary" style="padding: 7px 14px; font-size: 0.85rem; border-radius: 8px;">
          Reset
        </a>
      </div>

      <!-- Quick Preset Dates -->
      <div style="display: flex; gap: 6px; align-items: center; margin-left: auto; flex-wrap: wrap;">
        <span style="font-size: 0.75rem; font-weight: 700; color: var(--tp-text-muted, #64748b); text-transform: uppercase;">Range:</span>
        <button type="button" class="btn btn-sm btn-secondary tp-btn-secondary" style="font-size: 0.75rem; padding: 3px 9px;" onclick="setDateRange('today')">Today</button>
        <button type="button" class="btn btn-sm btn-secondary tp-btn-secondary" style="font-size: 0.75rem; padding: 3px 9px;" onclick="setDateRange('week')">This Week</button>
        <button type="button" class="btn btn-sm btn-secondary tp-btn-secondary" style="font-size: 0.75rem; padding: 3px 9px;" onclick="setDateRange('month')">This Month</button>
        <button type="button" class="btn btn-sm btn-secondary tp-btn-secondary" style="font-size: 0.75rem; padding: 3px 9px;" onclick="setDateRange('last_month')">Last Month</button>
      </div>
    </form>
  </div>"""

filter_section_replacement = """  <!-- =================================================================== -->
  <!-- 2. FILTER & AUDIT SCOPE BAR (Custom Range + FY + Quick Presets)     -->
  <!-- =================================================================== -->
  <div class="filter-card tp-card" style="background: var(--tp-surface-card, #ffffff); border-radius: 12px; border: 1px solid var(--tp-surface-border, #e2e8f0); padding: 18px 22px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
    <form method="get" action="" id="accountantFilterForm" style="display: flex; flex-direction: column; gap: 14px;">
      <input type="hidden" name="start_date" id="acc_start_date" value="{{ start_date }}">
      <input type="hidden" name="end_date" id="acc_end_date" value="{{ end_date }}">
      
      <div style="display: flex; flex-wrap: wrap; gap: 14px; align-items: center; justify-content: space-between;">
        <!-- Preset Pills Group -->
        <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
          <span style="font-size: 0.74rem; font-weight: 800; color: var(--tp-text-muted, #64748b); text-transform: uppercase; letter-spacing: 0.05em; margin-right: 4px;">Period:</span>
          <button type="button" class="btn btn-sm {% if active_period == 'today' %}btn-primary tp-btn-primary{% else %}btn-secondary tp-btn-secondary{% endif %}" style="font-size: 0.76rem; padding: 4px 10px; font-weight: 600; border-radius: 6px;" onclick="setDateRange('today')">Today</button>
          <button type="button" class="btn btn-sm {% if active_period == 'yesterday' %}btn-primary tp-btn-primary{% else %}btn-secondary tp-btn-secondary{% endif %}" style="font-size: 0.76rem; padding: 4px 10px; font-weight: 600; border-radius: 6px;" onclick="setDateRange('yesterday')">Yesterday</button>
          <button type="button" class="btn btn-sm {% if active_period == 'week' %}btn-primary tp-btn-primary{% else %}btn-secondary tp-btn-secondary{% endif %}" style="font-size: 0.76rem; padding: 4px 10px; font-weight: 600; border-radius: 6px;" onclick="setDateRange('week')">This Week</button>
          <button type="button" class="btn btn-sm {% if active_period == 'month' %}btn-primary tp-btn-primary{% else %}btn-secondary tp-btn-secondary{% endif %}" style="font-size: 0.76rem; padding: 4px 10px; font-weight: 600; border-radius: 6px;" onclick="setDateRange('month')">This Month</button>
          <button type="button" class="btn btn-sm {% if active_period == 'last_month' %}btn-primary tp-btn-primary{% else %}btn-secondary tp-btn-secondary{% endif %}" style="font-size: 0.76rem; padding: 4px 10px; font-weight: 600; border-radius: 6px;" onclick="setDateRange('last_month')">Last Month</button>
          <button type="button" class="btn btn-sm {% if active_period == 'this_fy' or active_period == 'fy' %}btn-primary tp-btn-primary{% else %}btn-secondary tp-btn-secondary{% endif %}" style="font-size: 0.76rem; padding: 4px 10px; font-weight: 600; border-radius: 6px;" onclick="setDateRange('fy')">This Financial Year (Apr–Mar)</button>
          <button type="button" id="customRangeToggleBtn" class="btn btn-sm {% if active_period == 'custom' %}btn-primary tp-btn-primary{% else %}btn-secondary tp-btn-secondary{% endif %}" style="font-size: 0.76rem; padding: 4px 12px; font-weight: 600; border-radius: 6px; display: inline-flex; align-items: center; gap: 4px;" onclick="toggleCustomRange()">
            <span>Custom Range</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
        </div>

        {% if branches|length > 1 %}
        <div style="display: flex; align-items: center; gap: 8px;">
          <label style="font-size: 0.75rem; font-weight: 700; color: var(--tp-text-muted, #64748b); text-transform: uppercase;">Branch:</label>
          <select name="branch" class="form-select tp-select form-select-sm" style="font-size: 0.82rem; padding: 4px 10px; border-radius: 6px; border: 1px solid var(--tp-surface-border, #cbd5e1); min-width: 160px;" onchange="this.form.submit()">
            <option value="">All Accessible Branches</option>
            {% for b in branches %}
            <option value="{{ b.id }}" {% if selected_branch_id == b.id %}selected{% endif %}>{{ b.name }}</option>
            {% endfor %}
          </select>
        </div>
        {% endif %}
      </div>

      <!-- Custom Date Inputs (Revealed when Custom is clicked or active) -->
      <div id="accountantCustomDateInputs" style="display: {% if active_period == 'custom' %}flex{% else %}none{% endif %}; gap: 12px; align-items: flex-end; flex-wrap: wrap; background: var(--tp-surface-bg, #f8fafc); border: 1px solid var(--tp-surface-border, #e2e8f0); padding: 12px 16px; border-radius: 8px; margin-top: 4px;">
        <div>
          <label style="display: block; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: var(--tp-text-muted, #64748b); margin-bottom: 4px;">From Date</label>
          <input type="date" name="from" id="accountantFromDate" class="form-control form-control-sm tp-input" value="{{ from_date|default:start_date }}" style="width: 155px; font-size: 0.82rem; height: 34px;">
        </div>
        <div>
          <label style="display: block; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: var(--tp-text-muted, #64748b); margin-bottom: 4px;">To Date</label>
          <input type="date" name="to" id="accountantToDate" class="form-control form-control-sm tp-input" value="{{ to_date|default:end_date }}" style="width: 155px; font-size: 0.82rem; height: 34px;">
        </div>
        <div style="display: flex; gap: 8px;">
          <button type="submit" class="btn btn-sm btn-primary tp-btn-primary" style="padding: 6px 16px; font-size: 0.82rem; font-weight: 700; border-radius: 6px; height: 34px;">
            Apply Custom Range
          </button>
          <a href="{% url 'accountant_dashboard' %}" class="btn btn-sm btn-secondary tp-btn-secondary" style="padding: 6px 14px; font-size: 0.82rem; border-radius: 6px; height: 34px; display: inline-flex; align-items: center;">
            Reset
          </a>
        </div>
      </div>
    </form>
  </div>"""

if filter_section_needle in html:
    html = html.replace(filter_section_needle, filter_section_replacement, 1)
    print("Replaced Filter Section with responsive custom date range UI!")

# 3. Replace JS setDateRange implementation
old_js_needle = """function setDateRange(period) {
  const today = new Date();
  const form = document.querySelector('.filter-card form');
  const startInput = form.querySelector('input[name="start_date"]');
  const endInput = form.querySelector('input[name="end_date"]');
  
  const formatDate = d => d.toISOString().split('T')[0];
  endInput.value = formatDate(today);

  if (period === 'today') {
    startInput.value = formatDate(today);
  } else if (period === 'week') {
    const day = today.getDay();
    const diff = today.getDate() - day + (day === 0 ? -6 : 1);
    const monday = new Date(today.setDate(diff));
    startInput.value = formatDate(monday);
  } else if (period === 'month') {
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    startInput.value = formatDate(firstDay);
  } else if (period === 'last_month') {
    const firstDay = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const lastDay = new Date(today.getFullYear(), today.getMonth(), 0);
    startInput.value = formatDate(firstDay);
    endInput.value = formatDate(lastDay);
  }
  form.submit();
}"""

new_js_replacement = """function toggleCustomRange() {
  const box = document.getElementById('accountantCustomDateInputs');
  if (box) {
    box.style.display = (box.style.display === 'none' || box.style.display === '') ? 'flex' : 'none';
    if (box.style.display === 'flex') {
      const fromInput = document.getElementById('accountantFromDate');
      if (fromInput) fromInput.focus();
    }
  }
}

function setDateRange(period) {
  const form = document.getElementById('accountantFilterForm');
  if (!form) return;
  const fromInput = document.getElementById('accountantFromDate');
  const toInput = document.getElementById('accountantToDate');
  const startInput = document.getElementById('acc_start_date');
  const endInput = document.getElementById('acc_end_date');

  if (period === 'custom') {
    toggleCustomRange();
    return;
  }

  const today = new Date();
  const formatYMD = d => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  };

  let s = new Date(today);
  let e = new Date(today);

  if (period === 'today') {
    s = today;
    e = today;
  } else if (period === 'yesterday') {
    s.setDate(today.getDate() - 1);
    e.setDate(today.getDate() - 1);
  } else if (period === 'week') {
    const day = today.getDay();
    const diff = today.getDate() - day + (day === 0 ? -6 : 1);
    s = new Date(today.getFullYear(), today.getMonth(), diff);
    e = today;
  } else if (period === 'month') {
    s = new Date(today.getFullYear(), today.getMonth(), 1);
    e = today;
  } else if (period === 'last_month') {
    s = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    e = new Date(today.getFullYear(), today.getMonth(), 0);
  } else if (period === 'fy') {
    if (today.getMonth() >= 3) {
      s = new Date(today.getFullYear(), 3, 1);
    } else {
      s = new Date(today.getFullYear() - 1, 3, 1);
    }
    e = today;
  }

  const sStr = formatYMD(s);
  const eStr = formatYMD(e);
  if (fromInput) fromInput.value = sStr;
  if (toInput) toInput.value = eStr;
  if (startInput) startInput.value = sStr;
  if (endInput) endInput.value = eStr;
  form.submit();
}

// Client-side date validation
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('accountantFilterForm');
  if (form) {
    form.addEventListener('submit', function(e) {
      const fromVal = document.getElementById('accountantFromDate') ? document.getElementById('accountantFromDate').value.trim() : '';
      const toVal = document.getElementById('accountantToDate') ? document.getElementById('accountantToDate').value.trim() : '';
      if (fromVal && toVal && fromVal > toVal) {
        alert('Validation Error: From Date cannot be after To Date.');
        e.preventDefault();
        return false;
      }
      if (fromVal && document.getElementById('acc_start_date')) document.getElementById('acc_start_date').value = fromVal;
      if (toVal && document.getElementById('acc_end_date')) document.getElementById('acc_end_date').value = toVal;
    });
  }
});"""

if old_js_needle in html:
    html = html.replace(old_js_needle, new_js_replacement, 1)
    print("Replaced JS date handling functions in dashboard.html!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated dashboard.html successfully!")
