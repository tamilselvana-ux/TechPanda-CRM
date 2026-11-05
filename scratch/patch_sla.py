import os

# 1. Update models.py
models_path = 'leads/models.py' if os.path.exists('leads/models.py') else 'CRM/leads/models.py'
with open(models_path, 'r', encoding='utf-8') as f:
    models_content = f.read()

sla_property = '''
    @property
    def sla_info(self):
        """
        Sales Head & Manager Visual SLA Escalation Timer.
        Evaluates elapsed response time since creation for uncontacted leads.
        """
        from django.utils import timezone
        # If contacted or converted, no active breach
        if self.status not in ('New', LeadStatus.NEW):
            return {
                'level': 'contacted',
                'badge_color': '#059669',
                'bg_color': '#ecfdf5',
                'border_color': '#a7f3d0',
                'text': 'Contacted',
                'is_breached': False
            }
        
        diff = timezone.now() - self.created_at
        total_seconds = diff.total_seconds()
        hours = total_seconds / 3600.0
        minutes = int(total_seconds / 60)

        if total_seconds < 1800:  # < 30m
            return {
                'level': 'fresh',
                'badge_color': '#0284c7',
                'bg_color': '#f0f9ff',
                'border_color': '#bae6fd',
                'text': f'⏱️ {minutes}m uncalled',
                'is_breached': False
            }
        elif total_seconds <= 7200:  # 30m - 2h
            return {
                'level': 'warning',
                'badge_color': '#d97706',
                'bg_color': '#fffbeb',
                'border_color': '#fde68a',
                'text': f'⚠️ {minutes}m uncalled',
                'is_breached': False
            }
        else:  # > 2h crimson breached
            if hours < 24:
                time_str = f"{hours:.1f}h"
            else:
                days = int(hours / 24)
                time_str = f"{days}d {int(hours % 24)}h"
            return {
                'level': 'breached',
                'badge_color': '#dc2626',
                'bg_color': '#fef2f2',
                'border_color': '#fecaca',
                'text': f'🚨 SLA Breached ({time_str})',
                'is_breached': True
            }
'''

target_model = "    @property\n    def last_three_calls(self):"
if target_model in models_content and "def sla_info(self):" not in models_content:
    models_content = models_content.replace(target_model, sla_property + "\n" + target_model, 1)
    with open(models_path, 'w', encoding='utf-8') as f:
        f.write(models_content)
    print("PATCHED_MODELS_SLA_INFO")
else:
    print("MODELS_SLA_INFO_ALREADY_PRESENT_OR_TARGET_NOT_FOUND")

# 2. Update views.py in manager_leads_list and admin_leads_list
views_path = 'leads/views.py' if os.path.exists('leads/views.py') else 'CRM/leads/views.py'
with open(views_path, 'r', encoding='utf-8') as f:
    views_content = f.read()

# In manager_leads_list:
mgr_filter_target = "    product_filter = request.GET.get('product', '').strip()"
mgr_filter_replacement = """    product_filter = request.GET.get('product', '').strip()\n    sla_filter = request.GET.get('sla', '').strip()"""

mgr_apply_target = """    if product_filter:\n        leads_qs = leads_qs.filter(product_id=product_filter)"""
mgr_apply_replacement = """    if product_filter:
        leads_qs = leads_qs.filter(product_id=product_filter)

    if sla_filter:
        now = timezone.now()
        if sla_filter == 'breached':
            two_hours_ago = now - timedelta(hours=2)
            leads_qs = leads_qs.filter(status='New', created_at__lte=two_hours_ago)
        elif sla_filter == 'warning':
            two_hours_ago = now - timedelta(hours=2)
            thirty_mins_ago = now - timedelta(minutes=30)
            leads_qs = leads_qs.filter(status='New', created_at__gte=two_hours_ago, created_at__lte=thirty_mins_ago)
        elif sla_filter == 'fresh':
            thirty_mins_ago = now - timedelta(minutes=30)
            leads_qs = leads_qs.filter(status='New', created_at__gt=thirty_mins_ago)"""

if mgr_filter_target in views_content and "sla_filter =" not in views_content:
    views_content = views_content.replace(mgr_filter_target, mgr_filter_replacement, 1)
    views_content = views_content.replace(mgr_apply_target, mgr_apply_replacement, 1)
    # Also pass sla_filter to context
    mgr_ctx_target = "'product_filter': product_filter,"
    mgr_ctx_replacement = "'product_filter': product_filter,\n        'sla_filter': sla_filter,"
    views_content = views_content.replace(mgr_ctx_target, mgr_ctx_replacement, 1)
    with open(views_path, 'w', encoding='utf-8') as f:
        f.write(views_content)
    print("PATCHED_VIEWS_MGR_SLA")
else:
    print("VIEWS_MGR_SLA_ALREADY_PATCHED_OR_TARGET_NOT_FOUND")

# 3. Update templates/manager/leads_list.html
tmpl_path = 'templates/manager/leads_list.html' if os.path.exists('templates/manager/leads_list.html') else 'CRM/templates/manager/leads_list.html'
with open(tmpl_path, 'r', encoding='utf-8') as f:
    tmpl_content = f.read()

# Add SLA Filter Pill Strip
sla_pill_strip = """
  <!-- Quick SLA Escalation Filter Pill Strip -->
  <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color, #e2e8f0);">
    <span style="font-size: 0.8rem; font-weight: 700; color: var(--tp-text-muted, #64748b); text-transform: uppercase; margin-right: 4px;">SLA Status:</span>
    <a href="?{% for k, v in request.GET.items %}{% if k != 'sla' and k != 'page' %}{{ k }}={{ v }}&{% endif %}{% endfor %}" class="badge tp-badge {% if not sla_filter %}active{% endif %}" style="padding: 4px 10px; border-radius: 6px; text-decoration: none; font-size: 0.78rem; font-weight: 600; border: 1px solid #cbd5e1; {% if not sla_filter %}background: #2563eb; color: #fff; border-color: #2563eb;{% else %}background: #f8fafc; color: #475569;{% endif %}">
      All SLA
    </a>
    <a href="?sla=breached{% for k, v in request.GET.items %}{% if k != 'sla' and k != 'page' %}&{{ k }}={{ v }}{% endif %}{% endfor %}" class="badge tp-badge {% if sla_filter == 'breached' %}active{% endif %}" style="padding: 4px 10px; border-radius: 6px; text-decoration: none; font-size: 0.78rem; font-weight: 700; border: 1px solid #fecaca; {% if sla_filter == 'breached' %}background: #dc2626; color: #fff; border-color: #dc2626;{% else %}background: #fef2f2; color: #b91c1c;{% endif %}">
      🚨 SLA Breached (&gt;2h Uncalled)
    </a>
    <a href="?sla=warning{% for k, v in request.GET.items %}{% if k != 'sla' and k != 'page' %}&{{ k }}={{ v }}{% endif %}{% endfor %}" class="badge tp-badge {% if sla_filter == 'warning' %}active{% endif %}" style="padding: 4px 10px; border-radius: 6px; text-decoration: none; font-size: 0.78rem; font-weight: 700; border: 1px solid #fde68a; {% if sla_filter == 'warning' %}background: #d97706; color: #fff; border-color: #d97706;{% else %}background: #fffbeb; color: #b45309;{% endif %}">
      ⚠️ Approaching Breach (30m - 2h)
    </a>
    <a href="?sla=fresh{% for k, v in request.GET.items %}{% if k != 'sla' and k != 'page' %}&{{ k }}={{ v }}{% endif %}{% endfor %}" class="badge tp-badge {% if sla_filter == 'fresh' %}active{% endif %}" style="padding: 4px 10px; border-radius: 6px; text-decoration: none; font-size: 0.78rem; font-weight: 600; border: 1px solid #bae6fd; {% if sla_filter == 'fresh' %}background: #0284c7; color: #fff; border-color: #0284c7;{% else %}background: #f0f9ff; color: #0369a1;{% endif %}">
      ⏱️ Fresh (&lt;30m)
    </a>
  </div>
"""

tmpl_form_start = '<form method="GET" class="filter-form">'
if tmpl_form_start in tmpl_content and "SLA Status:" not in tmpl_content:
    tmpl_content = tmpl_content.replace(tmpl_form_start, sla_pill_strip + "\n  " + tmpl_form_start, 1)
    print("ADDED_SLA_PILL_STRIP")

# Add SLA Column Header
old_th = '<th>Status</th>'
new_th = '<th>Status</th>\n          <th>Response SLA</th>'
if old_th in tmpl_content and "Response SLA" not in tmpl_content:
    tmpl_content = tmpl_content.replace(old_th, new_th, 1)
    print("ADDED_SLA_TH")

# Add SLA Column TD in row
old_td = '<td><span class="badge badge-{{ ld.status|lower|slugify }}">{{ ld.status }}</span></td>'
new_td = """<td><span class="badge badge-{{ ld.status|lower|slugify }}">{{ ld.status }}</span></td>
          <td>
            <span class="badge" style="background: {{ ld.sla_info.bg_color }}; color: {{ ld.sla_info.badge_color }}; border: 1px solid {{ ld.sla_info.border_color }}; font-weight: 700; font-size: 0.74rem; white-space: nowrap; padding: 3px 8px; border-radius: 6px;">
              {{ ld.sla_info.text }}
            </span>
          </td>"""
if old_td in tmpl_content and "{{ ld.sla_info.text }}" not in tmpl_content:
    tmpl_content = tmpl_content.replace(old_td, new_td, 1)
    print("ADDED_SLA_TD")

with open(tmpl_path, 'w', encoding='utf-8') as f:
    f.write(tmpl_content)

print("ALL_SLA_PATCHES_APPLIED")
