import re

dashboard_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\admin_dashboard\dashboard.html'
with open(dashboard_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Filter Toolbar
# Replace from '<!-- Top Quick Period Row -->' up to '<!-- SECTION 1:'
filter_regex = re.compile(
    r'<!-- Top Quick Period Row -->.*?<!-- SECTION 1: High-Velocity Operational Metrics -->',
    re.DOTALL
)

new_filter_html = '''<!-- TOP FILTER TOOLBAR (2-TIER EXECUTIVE ARCHITECTURE) -->
  <div class="tp-filter-toolbar-tier1" style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid var(--tp-surface-border, rgba(226, 232, 240, 0.7)); overflow: visible !important;">
    <div style="display: flex; align-items: center; gap: 18px; flex-wrap: wrap; overflow: visible !important;">
      <!-- Quick Period Presets -->
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 0.72rem; font-weight: 700; color: var(--tp-text-muted); text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap;">Quick Period:</span>
        <div style="display: inline-flex; gap: 5px; background: rgba(0,0,0,0.03); padding: 3px; border-radius: 8px; border: 1px solid var(--tp-surface-border, rgba(226, 232, 240, 0.6));">
          <a href="?period=all" class="btn btn-sm {% if period == 'all' or not period and not from_date and not to_date %}btn-primary tp-btn-primary{% else %}btn-secondary tp-btn-secondary{% endif %}" style="font-size: 0.775rem; padding: 4px 12px; border-radius: 6px; font-weight: 600;">All Time</a>
          <a href="?period=today" class="btn btn-sm {% if period == 'today' %}btn-primary tp-btn-primary{% else %}btn-secondary tp-btn-secondary{% endif %}" style="font-size: 0.775rem; padding: 4px 12px; border-radius: 6px; font-weight: 600;">Today</a>
          <a href="?period=week" class="btn btn-sm {% if period == 'week' %}btn-primary tp-btn-primary{% else %}btn-secondary tp-btn-secondary{% endif %}" style="font-size: 0.775rem; padding: 4px 12px; border-radius: 6px; font-weight: 600;">This Week</a>
          <a href="?period=month" class="btn btn-sm {% if period == 'month' %}btn-primary tp-btn-primary{% else %}btn-secondary tp-btn-secondary{% endif %}" style="font-size: 0.775rem; padding: 4px 12px; border-radius: 6px; font-weight: 600;">This Month</a>
        </div>
      </div>
      <!-- Date Range Picker -->
      <div class="tp-filter-field tp-filter-field-date" style="display: flex; align-items: center; gap: 8px; overflow: visible !important; min-width: 250px;">
        <span style="font-size: 0.72rem; font-weight: 700; color: var(--tp-text-muted); text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap;">Custom Range:</span>
        {% include "partials/date_range_picker.html" with from_name="from_date" to_name="to_date" from_val=from_date to_val=to_date %}
      </div>
    </div>

    <!-- Reset Filter Badge -->
    {% if from_date or to_date or manager_filter or telecaller_filter or branch_filter or channel_filter or status_filter or period and period != 'all' %}
    <a href="{% url 'admin_dashboard' %}" style="font-size: 0.775rem; font-weight: 700; color: #ef4444; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: 8px; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); transition: all 0.15s ease;">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      Reset Filters
    </a>
    {% endif %}
  </div>

  <!-- Tier 2: Entity & Dimension Filters (Sales Head, Telecaller, Branch, Channel, Status) -->
  <form method="GET" class="tp-compact-filter-grid" style="display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; width: 100%; margin-bottom: 24px; overflow: visible !important;">
    <div class="tp-filter-field" style="flex: 1 1 170px; min-width: 150px;">
      <label class="tp-field-label" style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--tp-text-muted); margin-bottom: 4px;">Sales Head</label>
      <select name="manager" class="form-select tp-select-compact" onchange="this.form.submit()">
        <option value="">All Sales Heads</option>
        {% for m in managers %}
        <option value="{{ m.id }}" {% if manager_filter == m.id|stringformat:"i" %}selected{% endif %}>{{ m.get_full_name|default:m.username }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="tp-filter-field" style="flex: 1 1 170px; min-width: 150px;">
      <label class="tp-field-label" style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--tp-text-muted); margin-bottom: 4px;">Telecaller</label>
      <select name="telecaller" class="form-select tp-select-compact" onchange="this.form.submit()">
        <option value="">All Telecallers</option>
        {% for t in telecallers %}
        <option value="{{ t.id }}" {% if telecaller_filter == t.id|stringformat:"i" %}selected{% endif %}>{{ t.get_full_name|default:t.username }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="tp-filter-field" style="flex: 1 1 150px; min-width: 140px;">
      <label class="tp-field-label" style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--tp-text-muted); margin-bottom: 4px;">Branch</label>
      <select name="branch" class="form-select tp-select-compact" onchange="this.form.submit()">
        <option value="">All Branches</option>
        {% for b in branches %}
        <option value="{{ b.id }}" {% if branch_filter == b.id|stringformat:"i" %}selected{% endif %}>{{ b.name }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="tp-filter-field" style="flex: 1 1 150px; min-width: 140px;">
      <label class="tp-field-label" style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--tp-text-muted); margin-bottom: 4px;">Channel</label>
      <select name="channel" class="form-select tp-select-compact" onchange="this.form.submit()">
        <option value="">All Channels</option>
        {% for c in channels %}
        <option value="{{ c.id }}" {% if channel_filter == c.id|stringformat:"i" %}selected{% endif %}>{{ c.name }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="tp-filter-field" style="flex: 1 1 150px; min-width: 140px;">
      <label class="tp-field-label" style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--tp-text-muted); margin-bottom: 4px;">Status</label>
      <select name="status" class="form-select tp-select-compact" onchange="this.form.submit()">
        <option value="">All Statuses</option>
        {% for code, label in statuses %}
        <option value="{{ code }}" {% if status_filter == code %}selected{% endif %}>{{ label }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="tp-filter-action" style="display: flex; gap: 8px; align-items: flex-end; margin-left: auto;">
      <button type="submit" class="btn btn-primary tp-btn-primary btn-sm" style="font-size: 0.775rem; font-weight: 700; height: 34px; padding: 0 16px; display: inline-flex; align-items: center; gap: 6px; border-radius: 8px;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
        Filter
      </button>
      <a href="{% url 'admin_dashboard' %}" class="btn btn-secondary tp-btn-secondary btn-sm" style="font-size: 0.775rem; font-weight: 600; height: 34px; padding: 0 12px; display: inline-flex; align-items: center; border-radius: 8px;" title="Reset Filters">
        Reset
      </a>
    </div>
  </form>
</div>

<!-- SECTION 1: High-Velocity Operational Metrics -->'''

content = filter_regex.sub(new_filter_html, content, count=1)

# 2. Update Section 1 and Section 2
# Pattern for Section 1 and Section 2
section_regex = re.compile(
    r'<!-- SECTION 1: High-Velocity Operational Metrics -->.*?<!-- SECTION 2: Visual Pipeline & Telecaller Performance Charts -->',
    re.DOTALL
)

new_sections_html = '''<!-- SECTION 1: High-Velocity Operational Metrics -->
<div class="tp-dashboard-section" style="margin-bottom: 24px;">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
    <h3 style="font-size: 1.05rem; font-weight: 800; color: var(--tp-text-primary); margin: 0; display: flex; align-items: center; gap: 8px; letter-spacing: -0.01em;">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--tp-primary-500, #3b82f6)" stroke-width="2.5"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path></svg>
      Operational Velocity & Workload
    </h3>
    <div style="display: flex; align-items: center; gap: 8px;">
      <span class="tp-live-pill" style="display: inline-flex; align-items: center; gap: 6px; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 9999px; background: rgba(16, 185, 129, 0.12); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.25);">
        <span style="width: 6px; height: 6px; border-radius: 50%; background: #10b981; display: inline-block;"></span>
        LIVE PIPELINE PULSE
      </span>
    </div>
  </div>

  <!-- Sub-Tier 1A: Primary Pipeline Inflow & Risk (4 Cards in balanced 4-column grid) -->
  <div style="margin-bottom: 14px;">
    <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
      <span style="font-size: 0.72rem; font-weight: 700; color: var(--tp-text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Pipeline Flow & Inflow Prioritization</span>
    </div>
    <div class="tp-kpi-tier-4 tp-stagger-container">
      <!-- Total Inbound Leads -->
      <a href="{% build_kpi_url 'admin_leads_list' 'view' 'all' kpi_label='Total Inbound Leads' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #3b82f6; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view all leads">
        <div class="kpi-info" style="flex: 1;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: var(--tp-text-muted);">Total Inbound Leads</h4>
            <span style="font-size: 0.65rem; font-weight: 700; color: #3b82f6; background: rgba(59, 130, 246, 0.1); padding: 1px 6px; border-radius: 4px;">Inflow</span>
          </div>
          <div class="kpi-value" style="color: var(--tp-primary-600, #2563eb); font-size: 1.75rem; font-weight: 800; font-variant-numeric: tabular-nums;">{{ total_leads }}</div>
          <div style="font-size: 0.7rem; color: var(--tp-text-muted); margin-top: 2px;">Filtered inflow</div>
        </div>
        <div class="kpi-icon-wrap blue" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(59, 130, 246, 0.12); color: #3b82f6; flex-shrink: 0; margin-left: 10px;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>
        </div>
      </a>

      <!-- New Unhandled Leads -->
      <a href="{% build_kpi_url 'admin_leads_list' 'status' 'New' kpi_label='New Leads' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #6366f1; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view new leads">
        <div class="kpi-info" style="flex: 1;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: var(--tp-text-muted);">New Unhandled Leads</h4>
            <span style="font-size: 0.65rem; font-weight: 700; color: #6366f1; background: rgba(99, 102, 241, 0.1); padding: 1px 6px; border-radius: 4px;">SLA Pending</span>
          </div>
          <div class="kpi-value" style="color: #6366f1; font-size: 1.75rem; font-weight: 800; font-variant-numeric: tabular-nums;">{{ new_leads }}</div>
          <div style="font-size: 0.7rem; color: var(--tp-text-muted); margin-top: 2px;">Needs first contact</div>
        </div>
        <div class="kpi-icon-wrap" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(99, 102, 241, 0.12); color: #6366f1; flex-shrink: 0; margin-left: 10px;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
        </div>
      </a>

      <!-- Active Pipeline Leads -->
      <a href="{% build_kpi_url 'admin_leads_list' 'status' 'active' kpi_label='Active Pipeline Leads' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #10b981; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view active leads">
        <div class="kpi-info" style="flex: 1;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: var(--tp-text-muted);">Active Pipeline Leads</h4>
            <span style="font-size: 0.65rem; font-weight: 700; color: #10b981; background: rgba(16, 185, 129, 0.1); padding: 1px 6px; border-radius: 4px;">In Progress</span>
          </div>
          <div class="kpi-value" style="color: #10b981; font-size: 1.75rem; font-weight: 800; font-variant-numeric: tabular-nums;">{{ active_leads }}</div>
          <div style="font-size: 0.7rem; color: var(--tp-text-muted); margin-top: 2px;">Active nurturing</div>
        </div>
        <div class="kpi-icon-wrap green" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(16, 185, 129, 0.12); color: #10b981; flex-shrink: 0; margin-left: 10px;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
        </div>
      </a>

      <!-- Overdue Follow-ups -->
      <a href="{% build_kpi_url 'admin_followups_list' 'status' 'overdue' kpi_label='Overdue Follow-ups' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #ef4444; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view overdue follow-ups">
        <div class="kpi-info" style="flex: 1;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: #ef4444;">Overdue Follow-ups</h4>
            <span style="font-size: 0.65rem; font-weight: 700; color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 1px 6px; border-radius: 4px;">Requires Action</span>
          </div>
          <div class="kpi-value" style="color: #ef4444; font-size: 1.75rem; font-weight: 800; font-variant-numeric: tabular-nums;">{{ overdue_followups }}</div>
          <div style="font-size: 0.7rem; color: #ef4444; opacity: 0.9; margin-top: 2px;">Missed scheduled calls</div>
        </div>
        <div class="kpi-icon-wrap rose" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(239, 68, 68, 0.12); color: #ef4444; flex-shrink: 0; margin-left: 10px;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon></svg>
        </div>
      </a>
    </div>
  </div>

  <!-- Sub-Tier 1B: Telecalling Velocity & Follow-ups (3 Cards in balanced 3-column grid) -->
  <div>
    <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
      <span style="font-size: 0.72rem; font-weight: 700; color: var(--tp-text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Telecaller Calling & Task Velocity</span>
    </div>
    <div class="tp-kpi-tier-3 tp-stagger-container">
      <!-- Total Calls Made -->
      <a href="{% build_kpi_url 'admin_calls_list' kpi_label='Total Calls Made' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #0284c7; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view all calls">
        <div class="kpi-info" style="flex: 1;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: var(--tp-text-muted);">Total Calls Made</h4>
            <span style="font-size: 0.65rem; font-weight: 700; color: #0284c7; background: rgba(2, 132, 199, 0.1); padding: 1px 6px; border-radius: 4px;">Dials</span>
          </div>
          <div class="kpi-value" style="color: #0284c7; font-size: 1.75rem; font-weight: 800; font-variant-numeric: tabular-nums;">{{ total_calls }}</div>
          <div style="font-size: 0.7rem; color: var(--tp-text-muted); margin-top: 2px;">Logged outbound calls</div>
        </div>
        <div class="kpi-icon-wrap blue" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(2, 132, 199, 0.12); color: #0284c7; flex-shrink: 0; margin-left: 10px;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
        </div>
      </a>

      <!-- Completed Calls -->
      <a href="{% build_kpi_url 'admin_calls_list' 'status' 'Completed' kpi_label='Completed Calls' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #10b981; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view completed calls">
        <div class="kpi-info" style="flex: 1;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: var(--tp-text-muted);">Completed Calls</h4>
            <span style="font-size: 0.65rem; font-weight: 700; color: #10b981; background: rgba(16, 185, 129, 0.1); padding: 1px 6px; border-radius: 4px;">Connected</span>
          </div>
          <div class="kpi-value" style="color: #10b981; font-size: 1.75rem; font-weight: 800; font-variant-numeric: tabular-nums;">{{ completed_calls }}</div>
          <div style="font-size: 0.7rem; color: var(--tp-text-muted); margin-top: 2px;">Conversation held</div>
        </div>
        <div class="kpi-icon-wrap green" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(16, 185, 129, 0.12); color: #10b981; flex-shrink: 0; margin-left: 10px;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
        </div>
      </a>

      <!-- Pending Follow-ups -->
      <a href="{% build_kpi_url 'admin_followups_list' 'status' 'pending' kpi_label='Pending Follow-ups' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #f59e0b; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view pending follow-ups">
        <div class="kpi-info" style="flex: 1;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: var(--tp-text-muted);">Pending Follow-ups</h4>
            <span style="font-size: 0.65rem; font-weight: 700; color: #f59e0b; background: rgba(245, 158, 11, 0.1); padding: 1px 6px; border-radius: 4px;">Upcoming</span>
          </div>
          <div class="kpi-value" style="color: #f59e0b; font-size: 1.75rem; font-weight: 800; font-variant-numeric: tabular-nums;">{{ pending_followups }}</div>
          <div style="font-size: 0.7rem; color: var(--tp-text-muted); margin-top: 2px;">Scheduled queue</div>
        </div>
        <div class="kpi-icon-wrap amber" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(245, 158, 11, 0.12); color: #f59e0b; flex-shrink: 0; margin-left: 10px;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        </div>
      </a>
    </div>
  </div>
</div>

<!-- SECTION 2: Admissions, Revenue & Fee Collections (5 Cards in balanced 5-column grid) -->
<div class="tp-dashboard-section" style="margin-bottom: 24px;">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
    <h3 style="font-size: 1.05rem; font-weight: 800; color: var(--tp-text-primary); margin: 0; display: flex; align-items: center; gap: 8px; letter-spacing: -0.01em;">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--tp-emerald-500, #10b981)" stroke-width="2.5"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
      Admissions, Revenue &amp; Fee Collections
    </h3>
    <a href="{% url 'admin_enrolled_students' %}" style="font-size: 0.8rem; font-weight: 700; color: var(--tp-primary-600, #2563eb); text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">
      View All Students &rarr;
    </a>
  </div>
  <div class="tp-kpi-tier-5 tp-stagger-container">
    <!-- Enrolled Students -->
    <a href="{% build_kpi_url 'admin_enrolled_students' kpi_label='Enrolled Students' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #3b82f6; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view enrolled students">
      <div class="kpi-info" style="flex: 1;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
          <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: var(--tp-text-muted);">Enrolled Students</h4>
          <span style="font-size: 0.65rem; font-weight: 700; color: #3b82f6; background: rgba(59, 130, 246, 0.1); padding: 1px 6px; border-radius: 4px;">Students</span>
        </div>
        <div class="kpi-value" style="color: var(--tp-text-primary, #0f172a); font-size: 1.75rem; font-weight: 800; font-variant-numeric: tabular-nums;">{{ total_enrolled }}</div>
        <div style="font-size: 0.7rem; color: var(--tp-text-muted); margin-top: 2px;">Total admissions</div>
      </div>
      <div class="kpi-icon-wrap blue" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(59, 130, 246, 0.12); color: #3b82f6; flex-shrink: 0; margin-left: 10px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>
      </div>
    </a>

    <!-- Total Revenue -->
    <a href="{% build_kpi_url 'admin_enrolled_students' kpi_label='Total Contracted Revenue' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #8b5cf6; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view total contracted revenue">
      <div class="kpi-info" style="flex: 1;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
          <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: var(--tp-text-muted);">Total Revenue</h4>
          <span style="font-size: 0.65rem; font-weight: 700; color: #8b5cf6; background: rgba(139, 92, 246, 0.1); padding: 1px 6px; border-radius: 4px;">Contracted</span>
        </div>
        <div class="kpi-value" style="color: var(--tp-text-primary, #0f172a); font-size: 1.65rem; font-weight: 800; font-variant-numeric: tabular-nums;">₹{{ total_revenue|floatformat:2 }}</div>
        <div style="font-size: 0.7rem; color: var(--tp-text-muted); margin-top: 2px;">Gross course fees</div>
      </div>
      <div class="kpi-icon-wrap" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(139, 92, 246, 0.12); color: #8b5cf6; flex-shrink: 0; margin-left: 10px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line></svg>
      </div>
    </a>

    <!-- Total Collections -->
    <a href="{% build_kpi_url 'admin_enrolled_students' 'payment_status' 'Fully Paid' kpi_label='Fully Paid Collections' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #10b981; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view verified collections">
      <div class="kpi-info" style="flex: 1;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
          <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: var(--tp-text-muted);">Total Collections</h4>
          <span style="font-size: 0.65rem; font-weight: 700; color: #10b981; background: rgba(16, 185, 129, 0.1); padding: 1px 6px; border-radius: 4px;">Realized</span>
        </div>
        <div class="kpi-value" style="color: #059669; font-size: 1.65rem; font-weight: 800; font-variant-numeric: tabular-nums;">₹{{ total_collections|floatformat:2 }}</div>
        <div style="font-size: 0.7rem; color: #059669; margin-top: 2px;">Verified collected</div>
      </div>
      <div class="kpi-icon-wrap green" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(16, 185, 129, 0.12); color: #10b981; flex-shrink: 0; margin-left: 10px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
      </div>
    </a>

    <!-- Outstanding Balance -->
    <a href="{% build_kpi_url 'admin_enrolled_students' 'payment_status' 'Partially Paid' kpi_label='Outstanding Balance' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #f59e0b; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view outstanding balance">
      <div class="kpi-info" style="flex: 1;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
          <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: var(--tp-text-muted);">Outstanding Balance</h4>
          <span style="font-size: 0.65rem; font-weight: 700; color: #f59e0b; background: rgba(245, 158, 11, 0.1); padding: 1px 6px; border-radius: 4px;">Receivables</span>
        </div>
        <div class="kpi-value" style="color: #d97706; font-size: 1.65rem; font-weight: 800; font-variant-numeric: tabular-nums;">₹{{ total_outstanding|floatformat:2 }}</div>
        <div style="font-size: 0.7rem; color: #d97706; margin-top: 2px;">Pending future dues</div>
      </div>
      <div class="kpi-icon-wrap amber" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(245, 158, 11, 0.12); color: #f59e0b; flex-shrink: 0; margin-left: 10px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
      </div>
    </a>

    <!-- Overdue Installments -->
    <a href="{% build_kpi_url 'admin_enrolled_students' 'payment_status' 'Overdue' kpi_label='Overdue Installments' %}" class="kpi-card tp-kpi-card tp-hover-lift" style="text-decoration: none; color: inherit; display: flex; border-top: 3px solid #ef4444; position: relative; overflow: hidden; padding: 14px 16px;" title="Click to view overdue installments">
      <div class="kpi-info" style="flex: 1;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
          <h4 style="margin: 0; font-size: 0.78rem; font-weight: 600; color: #ef4444;">Overdue Installments</h4>
          <span style="font-size: 0.65rem; font-weight: 700; color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 1px 6px; border-radius: 4px;">Overdue</span>
        </div>
        <div class="kpi-value" style="color: #dc2626; font-size: 1.75rem; font-weight: 800; font-variant-numeric: tabular-nums;">{{ total_overdue_installments }}</div>
        <div style="font-size: 0.7rem; color: #ef4444; opacity: 0.9; margin-top: 2px;">Delayed installments</div>
      </div>
      <div class="kpi-icon-wrap rose" style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(239, 68, 68, 0.12); color: #ef4444; flex-shrink: 0; margin-left: 10px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon></svg>
      </div>
    </a>
  </div>
</div>

<!-- SECTION 2: Visual Pipeline & Telecaller Performance Charts -->'''

content = section_regex.sub(new_sections_html, content, count=1)

with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Admin Dashboard template successfully updated!')
