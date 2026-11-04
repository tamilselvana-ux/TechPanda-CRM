path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\admin\pipeline_statuses_list.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update the table header: add "Active Leads" column
old_thead = """            <th>Type</th>
            <th>State</th>
            <th style="text-align: right;">Actions</th>"""

new_thead = """            <th>Type</th>
            <th>Active Leads</th>
            <th>State</th>
            <th style="text-align: right;">Actions</th>"""

if old_thead in html:
    html = html.replace(old_thead, new_thead, 1)
    print("Updated table header in pipeline_statuses_list.html!")

# 2. Update table row: add leads count and Delete button on EVERY row
old_row_actions = """            <td>
              {% if st.is_active %}
              <span class="badge badge-active" style="background: #dcfce7; color: #15803d; font-size: 0.75rem;">Active</span>
              {% else %}
              <span class="badge badge-inactive" style="background: #fee2e2; color: #b91c1c; font-size: 0.75rem;">Inactive</span>
              {% endif %}
            </td>
            <td style="text-align: right; white-space: nowrap;">
              <a href="{% url 'admin_pipeline_status_edit' st.pk %}" class="btn btn-secondary btn-sm" style="padding: 4px 8px; font-size: 0.75rem;">Edit</a>
              
              <form method="POST" action="{% url 'admin_pipeline_status_toggle' st.pk %}" style="display: inline;">
                {% csrf_token %}
                <button type="submit" class="btn btn-secondary btn-sm" style="padding: 4px 8px; font-size: 0.75rem;">
                  {% if st.is_active %}Disable{% else %}Enable{% endif %}
                </button>
              </form>

              {% if not st.is_system_default %}
              <form method="POST" action="{% url 'admin_pipeline_status_delete' st.pk %}" style="display: inline;" onsubmit="return confirm('Delete status {{ st.name }}? This cannot be undone.');">
                {% csrf_token %}
                <button type="submit" class="btn btn-sm" style="padding: 4px 8px; font-size: 0.75rem; color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); background: transparent;">Delete</button>
              </form>
              {% endif %}
            </td>"""

new_row_actions = """            <td>
              <span class="badge" style="background: {% if st.leads_count > 0 %}rgba(59, 130, 246, 0.12){% else %}var(--tp-surface-bg, #f1f5f9){% endif %}; color: {% if st.leads_count > 0 %}#2563eb{% else %}var(--tp-text-muted, #94a3b8){% endif %}; font-weight: 700; font-size: 0.75rem; padding: 4px 8px; border-radius: 6px;">
                {{ st.leads_count|default:0 }} lead{{ st.leads_count|pluralize }}
              </span>
            </td>
            <td>
              {% if st.is_active %}
              <span class="badge badge-active" style="background: #dcfce7; color: #15803d; font-size: 0.75rem;">Active</span>
              {% else %}
              <span class="badge badge-inactive" style="background: #fee2e2; color: #b91c1c; font-size: 0.75rem;">Inactive</span>
              {% endif %}
            </td>
            <td style="text-align: right; white-space: nowrap;">
              <div style="display: inline-flex; gap: 4px; align-items: center;">
                <a href="{% url 'admin_pipeline_status_edit' st.pk %}" class="btn btn-secondary btn-sm" style="padding: 4px 8px; font-size: 0.75rem;">Edit</a>
                
                <form method="POST" action="{% url 'admin_pipeline_status_toggle' st.pk %}" style="display: inline;">
                  {% csrf_token %}
                  <button type="submit" class="btn btn-secondary btn-sm" style="padding: 4px 8px; font-size: 0.75rem;">
                    {% if st.is_active %}Disable{% else %}Enable{% endif %}
                  </button>
                </form>

                <button type="button" class="btn btn-sm" style="padding: 4px 8px; font-size: 0.75rem; color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); background: transparent; border-radius: 4px;" onclick="openStatusDeleteModal('{{ st.pk }}', '{{ st.name|escapejs }}', {{ st.leads_count|default:0 }}, {{ st.is_system_default|yesno:'true,false' }})">
                  Delete
                </button>
              </div>
            </td>"""

if old_row_actions in html:
    html = html.replace(old_row_actions, new_row_actions, 1)
    print("Updated table rows with Delete button on EVERY row!")
else:
    print("Warning: old_row_actions exact string not found, checking...")

# 3. Add Modal at the end of block content
modal_code = """
<!-- Pipeline Status Delete Confirmation & Migration Modal -->
<div id="statusDeleteModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(4px); z-index: 1050; align-items: center; justify-content: center; padding: 16px;">
  <div style="background: var(--tp-surface-card, #ffffff); border: 1px solid var(--tp-surface-border, #e2e8f0); border-radius: 14px; width: 100%; max-width: 480px; box-shadow: 0 20px 40px rgba(0,0,0,0.2); overflow: hidden;">
    <div style="padding: 18px 22px; border-bottom: 1px solid var(--tp-surface-border, #e2e8f0); display: flex; justify-content: space-between; align-items: center;">
      <h3 style="font-size: 1.05rem; font-weight: 800; margin: 0; color: #dc2626;">Delete Pipeline Status</h3>
      <button type="button" style="background: none; border: none; font-size: 1.25rem; cursor: pointer; color: var(--tp-text-muted, #94a3b8);" onclick="closeStatusDeleteModal()">&times;</button>
    </div>
    <form id="statusDeleteForm" method="POST" action="" style="padding: 20px 22px;">
      {% csrf_token %}
      <p style="font-size: 0.88rem; color: var(--tp-text-secondary, #475569); margin: 0 0 14px 0; line-height: 1.45;">
        Are you sure you want to delete status <strong id="deleteStatusNameDisplay" style="color: var(--tp-text-primary, #0f172a);"></strong>?
      </p>

      <!-- Warning if leads currently exist in this status -->
      <div id="statusInUseAlert" style="display: none; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 12px 14px; margin-bottom: 16px;">
        <div style="font-weight: 700; font-size: 0.82rem; color: #b45309; margin-bottom: 4px;">
          Active Leads Detected: <span id="leadsCountDisplay">0</span> lead(s)
        </div>
        <p style="font-size: 0.78rem; color: #78350f; margin: 0 0 10px 0; line-height: 1.4;">
          This status cannot be left empty. Choose which status to reassign these leads to before deletion:
        </p>
        <label style="display: block; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #78350f; margin-bottom: 4px;">Move Leads To Status <span style="color: #ef4444;">*</span></label>
        <select name="reassign_to_status" id="reassignSelect" class="form-select form-select-sm" style="width: 100%; font-size: 0.82rem;">
          {% for opt in all_statuses %}
          <option value="{{ opt.name }}">{{ opt.name }} ({{ opt.stage_category }})</option>
          {% endfor %}
        </select>
      </div>

      <!-- Notice if status has 0 leads -->
      <div id="statusZeroLeadsAlert" style="display: none; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 10px 14px; margin-bottom: 16px;">
        <span style="font-size: 0.8rem; color: #047857; font-weight: 600;">
          ✓ 0 leads currently use this status. It can be safely removed.
        </span>
      </div>

      <!-- System Default Warning -->
      <div id="systemDefaultCaution" style="display: none; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 8px; padding: 10px 14px; margin-bottom: 16px;">
        <span style="font-size: 0.78rem; color: #b91c1c; font-weight: 600; line-height: 1.4; display: block;">
          ⚠️ System Status Notice: This status is flagged as system default. Deleting it will re-index all stages and remove it from CRM workflows.
        </span>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 10px;">
        <button type="button" class="btn btn-secondary tp-btn-secondary" onclick="closeStatusDeleteModal()">Cancel</button>
        <button type="submit" class="btn btn-danger" style="background: #dc2626; border-color: #dc2626; color: #ffffff; font-weight: 700; padding: 7px 18px; border-radius: 6px;">
          Confirm & Delete
        </button>
      </div>
    </form>
  </div>
</div>

<script>
function openStatusDeleteModal(pk, name, count, isSystem) {
  document.getElementById('statusDeleteForm').action = '/admin/settings/pipeline-statuses/' + pk + '/delete/';
  document.getElementById('deleteStatusNameDisplay').textContent = name;
  document.getElementById('leadsCountDisplay').textContent = count;

  const inUseAlert = document.getElementById('statusInUseAlert');
  const zeroAlert = document.getElementById('statusZeroLeadsAlert');
  const systemCaution = document.getElementById('systemDefaultCaution');
  const select = document.getElementById('reassignSelect');

  if (count > 0) {
    inUseAlert.style.display = 'block';
    zeroAlert.style.display = 'none';
    if (select) {
      select.setAttribute('required', 'required');
      // Hide own status option from dropdown
      Array.from(select.options).forEach(opt => {
        opt.style.display = (opt.value === name) ? 'none' : 'block';
      });
      // Select first visible option
      const firstVisible = Array.from(select.options).find(opt => opt.value !== name);
      if (firstVisible) select.value = firstVisible.value;
    }
  } else {
    inUseAlert.style.display = 'none';
    zeroAlert.style.display = 'block';
    if (select) select.removeAttribute('required');
  }

  if (isSystem) {
    systemCaution.style.display = 'block';
  } else {
    systemCaution.style.display = 'none';
  }

  document.getElementById('statusDeleteModal').style.display = 'flex';
}

function closeStatusDeleteModal() {
  document.getElementById('statusDeleteModal').style.display = 'none';
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeStatusDeleteModal();
});
</script>
"""

if '{% endblock %}' in html:
    html = html.replace('{% endblock %}', modal_code + '\n{% endblock %}', 1)
    print("Appended modal markup and JS to pipeline_statuses_list.html!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Finished updating pipeline_statuses_list.html successfully!")
