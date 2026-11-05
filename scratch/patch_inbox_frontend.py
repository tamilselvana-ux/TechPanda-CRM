import os

tmpl_path = 'chat/templates/chat/inbox.html' if os.path.exists('chat/templates/chat/inbox.html') else 'CRM/chat/templates/chat/inbox.html'
with open(tmpl_path, 'r', encoding='utf-8') as f:
    tmpl = f.read()

target_actions = '<div class="chat-header-actions">'
replacement_actions = """<div class="chat-header-actions">
                        <!-- Meta 24-Hour Policy Window Countdown Badge -->
                        <span id="metaWindowBadge" class="badge" style="display: none; font-size: 0.74rem; font-weight: 700; padding: 4px 10px; border-radius: 9999px; white-space: nowrap; margin-right: 6px;"></span>
                        <!-- 1-Click Course Kit Dispatcher -->
                        <button type="button" id="btnSendCourseKit" class="btn btn-sm" style="display: none; align-items: center; gap: 5px; font-weight: 700; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; background: #0284c7; color: #fff; border: none; cursor: pointer; margin-right: 8px;" onclick="sendCourseKitAction()">
                            📚 Send Course Kit
                        </button>"""

if target_actions in tmpl and "metaWindowBadge" not in tmpl:
    tmpl = tmpl.replace(target_actions, replacement_actions, 1)
    with open(tmpl_path, 'w', encoding='utf-8') as f:
        f.write(tmpl)
    print("PATCHED_INBOX_HTML")
else:
    print("INBOX_HTML_ALREADY_PATCHED_OR_NOT_FOUND")

js_path = 'chat/static/chat/js/inbox.js' if os.path.exists('chat/static/chat/js/inbox.js') else 'CRM/chat/static/chat/js/inbox.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# In loadMessages, call updateMetaWindowStatus
target_load = "const messages = await response.json();\n            renderMessages(messages);"
replacement_load = """const messages = await response.json();
            renderMessages(messages);
            if (typeof updateMetaWindowStatus === 'function') {
                updateMetaWindowStatus(conversationId);
            }"""

if target_load in js and "updateMetaWindowStatus(conversationId)" not in js:
    js = js.replace(target_load, replacement_load, 1)

helpers = """
// ==========================================
// 24-HOUR META WINDOW & COURSE KIT HANDLERS
// ==========================================
async function updateMetaWindowStatus(conversationId) {
    const badge = document.getElementById('metaWindowBadge');
    const kitBtn = document.getElementById('btnSendCourseKit');
    if (!badge) return;
    try {
        const res = await fetch(`/api/conversations/${conversationId}/meta-window/`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.success && data.meta_window) {
            const w = data.meta_window;
            badge.style.display = 'inline-flex';
            badge.style.background = w.bg_color;
            badge.style.color = w.badge_color;
            badge.style.border = `1px solid ${w.border_color}`;
            badge.textContent = w.text;
            if (kitBtn) kitBtn.style.display = 'inline-flex';
        }
    } catch(e) {
        console.warn("Failed to check meta window:", e);
    }
}

async function sendCourseKitAction() {
    if (!state.activeConversationId) return;
    const kitBtn = document.getElementById('btnSendCourseKit');
    if (kitBtn) {
        kitBtn.disabled = true;
        kitBtn.textContent = 'Sending Kit...';
    }
    try {
        const res = await fetch(`/api/conversations/${state.activeConversationId}/send-course-kit/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.CRM_CONFIG ? window.CRM_CONFIG.csrfToken : ''
            },
            body: JSON.stringify({ course_name: 'Full Stack Development' })
        });
        const data = await res.json();
        if (data.success) {
            showToast('📚 Course Kit & Syllabus dispatched to WhatsApp!');
            if (typeof loadMessages === 'function') {
                loadMessages(state.activeConversationId);
            }
        } else {
            showToast(data.error || 'Failed to send Course Kit', 'error');
        }
    } catch(e) {
        showToast('Error dispatching Course Kit', 'error');
    } finally {
        if (kitBtn) {
            kitBtn.disabled = false;
            kitBtn.innerHTML = '📚 Send Course Kit';
        }
    }
}
"""

if "function updateMetaWindowStatus" not in js:
    js += "\n" + helpers
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print("PATCHED_INBOX_JS")
else:
    print("INBOX_JS_ALREADY_PATCHED")
