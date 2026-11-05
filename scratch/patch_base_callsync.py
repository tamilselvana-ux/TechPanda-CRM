import os

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\base.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """          <!-- 3D Isometric Theme Toggle Coin -->"""

replacement = """          <!-- CallSync Phone Connectivity Pulse (Phase 1, Item 141) -->
          {% if user.is_authenticated and user.role == "TELECALLER" %}
          <div id="tp-callsync-status-pill"
               class="tp-callsync-pill"
               title="CallSync Phone Status: Checking..."
               style="display: inline-flex; align-items: center; gap: 5px; padding: 4px 10px; border-radius: 20px; font-size: 0.73rem; font-weight: 700; background: rgba(100, 116, 139, 0.12); color: var(--text-muted); border: 1px solid rgba(100, 116, 139, 0.25); margin-right: 6px;">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>
            <span class="tp-callsync-dot" style="width: 7px; height: 7px; border-radius: 50%; background: #94a3b8; display: inline-block;"></span>
            <span id="tp-callsync-text">CallSync...</span>
          </div>
          {% endif %}

          <!-- 3D Isometric Theme Toggle Coin -->"""

assert target in content, "target not found in base.html"
content = content.replace(target, replacement, 1)

target_script = """  <!-- 3D Cinematic Interactive Micro-Engine -->"""

replacement_script = """  <script>
    function updateCallSyncStatus() {
      var pill = document.getElementById('tp-callsync-status-pill');
      if (!pill) return;
      fetch("{% url 'check_device_status' %}")
        .then(function(res) { return res.json(); })
        .then(function(data) {
          var dot = pill.querySelector('.tp-callsync-dot');
          var text = document.getElementById('tp-callsync-text');
          if (!data.has_device) {
            pill.style.background = 'rgba(239, 68, 68, 0.1)';
            pill.style.borderColor = 'rgba(239, 68, 68, 0.35)';
            pill.style.color = '#ef4444';
            pill.title = 'No CallSync phone paired. Please log into the Android app.';
            if (dot) dot.style.background = '#ef4444';
            if (text) text.textContent = 'Phone Unpaired';
          } else if (data.is_online) {
            pill.style.background = 'rgba(16, 185, 129, 0.12)';
            pill.style.borderColor = 'rgba(16, 185, 129, 0.35)';
            pill.style.color = '#059669';
            var batt = (data.battery_percent !== null && data.battery_percent !== undefined) ? ' (' + data.battery_percent + '%' + (data.is_charging ? '⚡' : '') + ')' : '';
            pill.title = 'CallSync Android Phone Connected! Synced ' + (data.last_seen_seconds_ago || 0) + 's ago' + batt;
            if (dot) dot.style.background = '#10b981';
            if (text) text.textContent = 'Ready' + batt;
          } else {
            pill.style.background = 'rgba(245, 158, 11, 0.12)';
            pill.style.borderColor = 'rgba(245, 158, 11, 0.35)';
            pill.style.color = '#d97706';
            var minAgo = data.last_seen_seconds_ago ? Math.round(data.last_seen_seconds_ago / 60) + 'm ago' : 'never';
            pill.title = 'Phone Offline! Last seen ' + minAgo + '. Please wake or open the CallSync app.';
            if (dot) dot.style.background = '#f59e0b';
            if (text) text.textContent = 'Phone Asleep';
          }
        })
        .catch(function() {});
    }
    if (document.getElementById('tp-callsync-status-pill')) {
      updateCallSyncStatus();
      setInterval(updateCallSyncStatus, 20000);
    }
  </script>
  <!-- 3D Cinematic Interactive Micro-Engine -->"""

assert target_script in content, "target_script not found in base.html"
content = content.replace(target_script, replacement_script, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated base.html with CallSync Heartbeat status pill and poller")
