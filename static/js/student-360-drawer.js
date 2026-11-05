/**
 * iTechPanda CRM - Unified 360° Student Admissions Drawer
 * Consolidated multi-channel timeline: Calls, WhatsApp, Payments, Notes, Status.
 */

let currentDrawerData = null;
let currentDrawerTab = 'timeline';

async function openStudent360Drawer(leadId) {
  const drawer = document.getElementById('student360Drawer');
  const backdrop = document.getElementById('student360Backdrop');
  const loading = document.getElementById('drawerLoading');
  const list = document.getElementById('drawerTimelineList');
  const empty = document.getElementById('drawerEmpty');

  if (!drawer || !backdrop) return;

  // Show drawer and backdrop immediately
  backdrop.style.display = 'block';
  setTimeout(() => { backdrop.style.opacity = '1'; }, 10);
  drawer.style.right = '0px';

  // Show loading skeleton
  loading.style.display = 'block';
  list.style.display = 'none';
  empty.style.display = 'none';

  try {
    const res = await fetch(`/leads/${leadId}/360-data/`, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Failed to load student data');

    currentDrawerData = data;
    renderDrawerHeader(data.student);
    renderDrawerStats(data.summary);
    renderDrawerTimeline(data.timeline, currentDrawerTab);

    loading.style.display = 'none';
    if (data.timeline && data.timeline.length > 0) {
      list.style.display = 'block';
    } else {
      empty.style.display = 'block';
    }
  } catch (err) {
    console.error("Error opening Student 360 Drawer:", err);
    loading.innerHTML = `
      <div style="color: #dc2626; font-weight: 700; font-size: 0.9rem;">⚠️ Failed to load student timeline</div>
      <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">${err.message || 'Server error occurred'}</div>
      <button type="button" class="btn btn-sm btn-secondary" style="margin-top: 12px;" onclick="openStudent360Drawer(${leadId})">Retry</button>
    `;
  }
}

function closeStudent360Drawer() {
  const drawer = document.getElementById('student360Drawer');
  const backdrop = document.getElementById('student360Backdrop');
  if (drawer) drawer.style.right = '-560px';
  if (backdrop) {
    backdrop.style.opacity = '0';
    setTimeout(() => { backdrop.style.display = 'none'; }, 250);
  }
}

function renderDrawerHeader(student) {
  if (!student) return;
  const nameEl = document.getElementById('drawerStudentName');
  const avatarEl = document.getElementById('drawerStudentAvatar');
  const statusEl = document.getElementById('drawerStatusBadge');
  const phoneEl = document.getElementById('drawerStudentPhone');
  const courseEl = document.getElementById('drawerStudentCourse');
  const btnCall = document.getElementById('drawerBtnCall');
  const btnWA = document.getElementById('drawerBtnWhatsApp');
  const btnEnroll = document.getElementById('drawerBtnEnroll');
  const btnEnrollText = document.getElementById('drawerBtnEnrollText');

  if (nameEl) nameEl.textContent = student.name || 'Unknown Student';
  if (avatarEl) {
    avatarEl.textContent = (student.name || 'S').trim().charAt(0).toUpperCase();
  }
  if (statusEl) {
    statusEl.textContent = student.status || 'New';
  }
  if (phoneEl) {
    phoneEl.textContent = student.phone || '';
  }
  if (courseEl) {
    courseEl.textContent = `${student.course} (${student.branch})`;
  }

  // Quick Action Buttons
  if (btnCall) {
    btnCall.onclick = () => {
      if (typeof openCallDialer === 'function') {
        openCallDialer(student.id, student.name, student.phone);
      } else {
        window.location.href = `tel:${student.phone}`;
      }
    };
  }

  if (btnWA) {
    const cleanPhone = (student.phone || '').replace(/\D/g, '');
    btnWA.href = `https://wa.me/91${cleanPhone.slice(-10)}`;
  }

  if (btnEnroll) {
    btnEnroll.href = `/leads/${student.id}/enroll/`;
    if (student.enrollment_number) {
      btnEnrollText.textContent = `Enrolled (${student.enrollment_number})`;
      btnEnroll.className = 'btn btn-sm btn-secondary';
    } else {
      btnEnrollText.textContent = 'Enroll / Collect Fee';
      btnEnroll.className = 'btn btn-sm btn-primary';
    }
  }
}

function renderDrawerStats(summary) {
  if (!summary) return;
  const paidEl = document.getElementById('drawerStatPaid');
  const balEl = document.getElementById('drawerStatBalance');
  const callsEl = document.getElementById('drawerStatCalls');

  if (paidEl) paidEl.textContent = `₹${(summary.total_paid || 0).toLocaleString('en-IN')}`;
  if (balEl) balEl.textContent = `₹${(summary.balance_due || 0).toLocaleString('en-IN')}`;
  if (callsEl) callsEl.textContent = summary.total_calls || 0;
}

function switchDrawerTab(tab) {
  currentDrawerTab = tab;
  const tabBtns = document.querySelectorAll('.tab-btn-360');
  tabBtns.forEach(btn => {
    btn.style.borderBottomColor = 'transparent';
    btn.style.color = '#64748b';
    btn.style.fontWeight = '600';
  });

  const activeBtn = event ? event.target.closest('.tab-btn-360') : null;
  if (activeBtn) {
    activeBtn.style.borderBottomColor = '#2563eb';
    activeBtn.style.color = '#2563eb';
    activeBtn.style.fontWeight = '700';
  }

  if (currentDrawerData) {
    renderDrawerTimeline(currentDrawerData.timeline, tab);
  }
}

function renderDrawerTimeline(events, filterTab) {
  const itemsContainer = document.getElementById('drawerTimelineItems');
  const empty = document.getElementById('drawerEmpty');
  const list = document.getElementById('drawerTimelineList');
  if (!itemsContainer) return;

  let filtered = events || [];
  if (filterTab === 'calls') {
    filtered = filtered.filter(e => e.type === 'call');
  } else if (filterTab === 'whatsapp') {
    filtered = filtered.filter(e => e.type === 'whatsapp');
  } else if (filterTab === 'payments') {
    filtered = filtered.filter(e => e.type === 'payment' || e.type === 'enrollment');
  }

  if (filtered.length === 0) {
    itemsContainer.innerHTML = '';
    list.style.display = 'none';
    empty.style.display = 'block';
    return;
  }

  list.style.display = 'block';
  empty.style.display = 'none';

  itemsContainer.innerHTML = filtered.map(item => `
    <div class="timeline-item-360">
      <div class="node-icon" style="background: ${item.color || '#2563eb'};"></div>
      <div class="timeline-card-360">
        <div style="display: flex; justify-content: space-between; align-items: baseline; gap: 8px;">
          <strong style="font-size: 0.88rem; color: #1e293b;">${item.title}</strong>
          <span style="font-size: 0.72rem; color: #94a3b8; white-space: nowrap;">${item.display_time}</span>
        </div>
        <div style="font-size: 0.8rem; color: #475569; margin-top: 3px;">
          ${item.description || ''}
        </div>
        ${item.notes ? `
          <div style="margin-top: 6px; padding: 6px 10px; background: ${item.bg_color || '#f8fafc'}; border-radius: 6px; font-size: 0.78rem; color: #334155; border-left: 3px solid ${item.color || '#2563eb'};">
            ${item.notes}
          </div>
        ` : ''}
        ${item.recording_url ? `
          <div style="margin-top: 8px;">
            <audio controls src="${item.recording_url}" style="width: 100%; height: 32px;"></audio>
          </div>
        ` : ''}
      </div>
    </div>
  `).join('');
}

// Global Event Delegation & Esc Key Listener
document.addEventListener('DOMContentLoaded', () => {
  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('[data-open-360]');
    if (trigger) {
      e.preventDefault();
      const leadId = trigger.getAttribute('data-open-360');
      if (leadId) openStudent360Drawer(leadId);
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeStudent360Drawer();
    }
  });
});
