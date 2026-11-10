fpath = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\fb_leads\templates\fb_leads\leads.html"
with open(fpath, "r", encoding="utf-8") as f:
    html = f.read()

target_btn = '''  <div style="display: flex; gap: 10px; align-items: center;">
    <a href="{% url 'fb_leads:fb_accounts' %}" class="btn btn-secondary">⚙ Manage Accounts & Pages</a>
    <form method="post" action="{% url 'fb_leads:facebook_leads_sync' %}" style="margin: 0;">
      {% csrf_token %}
      <button type="submit" class="btn btn-primary" {% if not configured %}disabled title="Add FB_PAGE_TOKEN and FB_PAGE_ID to .env first"{% endif %}>⟳ Sync All Leads</button>
    </form>
  </div>'''

replacement_btn = '''  <div style="display: flex; gap: 10px; align-items: center;">
    <a href="{% url 'fb_leads:fb_accounts' %}" class="btn btn-secondary">⚙ Manage Accounts & Pages</a>
    <button type="button" class="btn btn-primary" onclick="openSyncModal()" {% if not configured %}disabled title="Add FB_PAGE_TOKEN and FB_PAGE_ID to .env first"{% endif %}>⟳ Sync Leads</button>
  </div>'''

modal_and_js = '''
<!-- Sync Leads Date Filter Modal -->
<div id="syncLeadsModal" style="display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.6); z-index: 9999; align-items: center; justify-content: center; backdrop-filter: blur(2px);">
  <div style="background: #ffffff; border-radius: 14px; width: 100%; max-width: 480px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); overflow: hidden; margin: 16px; border: 1px solid #e2e8f0;">
    <div style="padding: 16px 20px; background: #0f172a; color: #ffffff; display: flex; justify-content: space-between; align-items: center;">
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 1.2rem;">⚡</span>
        <h3 style="margin: 0; font-size: 1.1rem; font-weight: 700; color: #ffffff;">Sync Facebook Leads</h3>
      </div>
      <button type="button" onclick="closeSyncModal()" style="background: none; border: none; color: #94a3b8; font-size: 1.4rem; cursor: pointer; line-height: 1;">&times;</button>
    </div>

    <form method="post" action="{% url 'fb_leads:facebook_leads_sync' %}" id="syncLeadsForm" onsubmit="handleSyncSubmit(event)" style="padding: 20px;">
      {% csrf_token %}
      <p style="font-size: 0.88rem; color: #475569; margin-top: 0; margin-bottom: 16px;">
        Choose the timeframe for lead synchronization. Filtering by date prevents re-importing old or deleted historical records.
      </p>

      <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 18px;">
        <label style="display: flex; align-items: center; gap: 10px; padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 8px; cursor: pointer; background: #f8fafc; transition: all 0.2s;">
          <input type="radio" name="sync_mode" value="today" checked onchange="toggleCustomDates(this.value)">
          <div>
            <div style="font-weight: 600; font-size: 0.9rem; color: #0f172a;">Today Only</div>
            <div style="font-size: 0.78rem; color: #64748b;">Sync leads submitted today (from 00:00:00 to now)</div>
          </div>
        </label>

        <label style="display: flex; align-items: center; gap: 10px; padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 8px; cursor: pointer; background: #f8fafc; transition: all 0.2s;">
          <input type="radio" name="sync_mode" value="yesterday" onchange="toggleCustomDates(this.value)">
          <div>
            <div style="font-weight: 600; font-size: 0.9rem; color: #0f172a;">Yesterday & Today</div>
            <div style="font-size: 0.78rem; color: #64748b;">Last 48 hours of lead ad submissions</div>
          </div>
        </label>

        <label style="display: flex; align-items: center; gap: 10px; padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 8px; cursor: pointer; background: #f8fafc; transition: all 0.2s;">
          <input type="radio" name="sync_mode" value="7days" onchange="toggleCustomDates(this.value)">
          <div>
            <div style="font-weight: 600; font-size: 0.9rem; color: #0f172a;">Last 7 Days</div>
            <div style="font-size: 0.78rem; color: #64748b;">All submissions from the past week</div>
          </div>
        </label>

        <label style="display: flex; align-items: center; gap: 10px; padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 8px; cursor: pointer; background: #f8fafc; transition: all 0.2s;">
          <input type="radio" name="sync_mode" value="custom" onchange="toggleCustomDates(this.value)">
          <div>
            <div style="font-weight: 600; font-size: 0.9rem; color: #0f172a;">Custom Date Range</div>
            <div style="font-size: 0.78rem; color: #64748b;">Specify exact start and end dates</div>
          </div>
        </label>

        <div id="customDateContainer" style="display: none; padding: 12px; background: #f1f5f9; border-radius: 8px; margin-top: 4px;">
          <div style="display: flex; gap: 10px;">
            <div style="flex: 1;">
              <label style="font-size: 0.78rem; font-weight: 600; color: #475569; display: block; margin-bottom: 4px;">Start Date</label>
              <input type="date" name="start_date" id="syncStartDate" class="form-control" style="width: 100%; font-size: 0.85rem; padding: 6px 10px;">
            </div>
            <div style="flex: 1;">
              <label style="font-size: 0.78rem; font-weight: 600; color: #475569; display: block; margin-bottom: 4px;">End Date</label>
              <input type="date" name="end_date" id="syncEndDate" class="form-control" style="width: 100%; font-size: 0.85rem; padding: 6px 10px;">
            </div>
          </div>
        </div>

        <label style="display: flex; align-items: center; gap: 10px; padding: 10px 14px; border: 1px solid #fed7aa; border-radius: 8px; cursor: pointer; background: #fff7ed; transition: all 0.2s;">
          <input type="radio" name="sync_mode" value="all" onchange="toggleCustomDates(this.value)">
          <div>
            <div style="font-weight: 600; font-size: 0.9rem; color: #c2410c;">All Time (Full Historical Sync)</div>
            <div style="font-size: 0.78rem; color: #9a3412;">Pulls every lead from the beginning of all ad forms</div>
          </div>
        </label>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #e2e8f0; padding-top: 14px;">
        <button type="button" class="btn btn-secondary" onclick="closeSyncModal()">Cancel</button>
        <button type="submit" id="submitSyncBtn" class="btn btn-primary" style="display: flex; align-items: center; gap: 8px;">
          <span id="syncBtnIcon">⟳</span>
          <span id="syncBtnText">Start Lead Sync</span>
        </button>
      </div>
    </form>
  </div>
</div>

<script>
function openSyncModal() {
  const modal = document.getElementById('syncLeadsModal');
  if (modal) {
    modal.style.display = 'flex';
  }
}

function closeSyncModal() {
  const modal = document.getElementById('syncLeadsModal');
  if (modal) {
    modal.style.display = 'none';
  }
}

function toggleCustomDates(mode) {
  const container = document.getElementById('customDateContainer');
  if (container) {
    if (mode === 'custom') {
      container.style.display = 'block';
    } else {
      container.style.display = 'none';
    }
  }
}

function handleSyncSubmit(e) {
  const btn = document.getElementById('submitSyncBtn');
  const text = document.getElementById('syncBtnText');
  const icon = document.getElementById('syncBtnIcon');
  if (btn && text) {
    btn.disabled = true;
    text.innerText = 'Synchronizing with Meta...';
    if (icon) icon.innerText = '⏳';
  }
}

// Close modal on Escape
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeSyncModal();
});
</script>
'''

html_norm = html.replace('\r\n', '\n')
target_btn_norm = target_btn.replace('\r\n', '\n')
replacement_btn_norm = replacement_btn.replace('\r\n', '\n')

if target_btn_norm in html_norm:
    html_norm = html_norm.replace(target_btn_norm, replacement_btn_norm, 1)
    # append modal before {% endblock %}
    html_norm = html_norm.replace('{% endblock %}', modal_and_js.strip() + '\n{% endblock %}', 1)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(html_norm)
    print("Updated leads.html with sync modal successfully")
else:
    print("target_btn not found in leads.html")
