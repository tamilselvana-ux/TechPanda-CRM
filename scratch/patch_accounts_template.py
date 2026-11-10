fpath = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\fb_leads\templates\fb_leads\accounts.html"
with open(fpath, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update the table header
old_thead = '''            <tr style="border-bottom: 2px solid var(--border-color, #e2e8f0); text-align: left; font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">
              <th style="padding: 10px 12px; width: 22%;">Page Name & ID</th>
              <th style="padding: 10px 12px; width: 18%;">Assigned Branch</th>
              <th style="padding: 10px 12px; width: 24%;">Auto-Sync Engine</th>
              <th style="padding: 10px 12px; width: 12%;">Webhook</th>
              <th style="padding: 10px 12px; width: 14%;">Last Sync Status</th>
              <th style="padding: 10px 12px; text-align: right; width: 10%;">Actions</th>
            </tr>'''

new_thead = '''            <tr style="border-bottom: 2px solid var(--border-color, #e2e8f0); text-align: left; font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">
              <th style="padding: 10px 12px; width: 20%;">Page Name & ID</th>
              <th style="padding: 10px 12px; width: 15%;">Assigned Branch</th>
              <th style="padding: 10px 12px; width: 18%;">Auto-Sync Engine</th>
              <th style="padding: 10px 12px; width: 16%;">Sync Cutoff Date</th>
              <th style="padding: 10px 12px; width: 10%;">Webhook</th>
              <th style="padding: 10px 12px; width: 12%;">Last Sync Status</th>
              <th style="padding: 10px 12px; text-align: right; width: 9%;">Actions</th>
            </tr>'''

# 2. Add the cutoff column cell in the row (after Auto-Sync Engine)
old_cell_marker = '''              <!-- Webhook Sync -->
              <td style="padding: 12px;">'''

new_cutoff_cell = '''              <!-- Sync Cutoff Date Shield -->
              <td style="padding: 12px;">
                <div style="display: flex; flex-direction: column; gap: 4px;">
                  <input type="date" id="cutoffDate-{{ page.id }}" value="{{ page.sync_cutoff_date|date:'Y-m-d' }}" 
                         class="form-control" style="font-size: 0.78rem; padding: 3px 6px; width: 100%; max-width: 140px;"
                         onchange="updatePageCutoff({{ page.id }}, this.value)"
                         title="Historical Cutoff: leads submitted before this date will never be synced">
                  <span id="cutoffStatus-{{ page.id }}" style="font-size: 0.72rem; color: {% if page.sync_cutoff_date %}#059669{% else %}#94a3b8{% endif %}; font-weight: 500;">
                    {% if page.sync_cutoff_date %}Shielded: from {{ page.sync_cutoff_date|date:"d M Y" }}{% else %}No cutoff (all leads){% endif %}
                  </span>
                </div>
              </td>

              <!-- Webhook Sync -->
              <td style="padding: 12px;">'''

# 3. Add JS function
js_cutoff = '''
function updatePageCutoff(pageId, dateStr) {
  const statusEl = document.getElementById(`cutoffStatus-${pageId}`);
  if (statusEl) {
    statusEl.innerText = "Saving...";
    statusEl.style.color = "#2563eb";
  }

  const formData = new FormData();
  formData.append("sync_cutoff_date", dateStr);

  fetch(`/facebook-leads/pages/${pageId}/cutoff/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest",
    },
    body: formData,
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        if (statusEl) {
          statusEl.innerText = data.sync_cutoff_date ? `Shielded: from ${data.sync_cutoff_date}` : "No cutoff (all leads)";
          statusEl.style.color = data.sync_cutoff_date ? "#059669" : "#94a3b8";
        }
      } else {
        alert(data.error || "Failed to update cutoff date");
      }
    })
    .catch(err => {
      console.error(err);
      alert("Network error updating cutoff date");
    });
}
'''

html_norm = html.replace('\r\n', '\n')
old_thead_norm = old_thead.replace('\r\n', '\n')
new_thead_norm = new_thead.replace('\r\n', '\n')
old_cell_norm = old_cell_marker.replace('\r\n', '\n')
new_cutoff_norm = new_cutoff_cell.replace('\r\n', '\n')

if old_thead_norm in html_norm:
    html_norm = html_norm.replace(old_thead_norm, new_thead_norm, 1)
    print("Replaced table header in accounts.html")

if old_cell_norm in html_norm:
    html_norm = html_norm.replace(old_cell_norm, new_cutoff_norm)
    print("Added cutoff date cell in accounts.html")

# Append JS before </script>
last_script_end = html_norm.rfind('</script>')
if last_script_end != -1:
    html_norm = html_norm[:last_script_end] + js_cutoff + html_norm[last_script_end:]
    print("Added updatePageCutoff JS function in accounts.html")

with open(fpath, "w", encoding="utf-8") as f:
    f.write(html_norm)
print("Updated accounts.html successfully")
