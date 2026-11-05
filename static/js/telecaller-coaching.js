/**
 * iTechPanda CRM - Real-Time AI Objection Coaching Engine
 * Listens to live call triggers and surfaces instant rebuttals, talking points,
 * and pitch strategies to telecallers and counselors during active calls.
 */

let coachingDebounceTimer;

async function triggerObjectionCoach(categoryCode, speechSnippet) {
  const coachCard = document.getElementById('aiCoachCard');
  const coachTitle = document.getElementById('aiCoachTitle');
  const coachRebuttal = document.getElementById('aiCoachRebuttal');
  const coachPoints = document.getElementById('aiCoachPoints');
  const coachAction = document.getElementById('aiCoachAction');

  if (!coachCard) return;

  try {
    const res = await fetch('/calls/api/coaching/analyze/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.getCsrfToken ? window.getCsrfToken() : ''
      },
      body: JSON.stringify({
        category: categoryCode || '',
        speech_text: speechSnippet || ''
      })
    });

    if (!res.ok) return;
    const data = await res.json();
    if (!data.success) return;

    coachCard.style.display = 'block';

    if (coachTitle) {
      coachTitle.innerHTML = `<span style="font-size: 1.1rem; margin-right: 4px;">${data.icon || '🤖'}</span> <strong>${data.category}</strong>`;
    }

    if (coachRebuttal) {
      coachRebuttal.innerHTML = `<em>"${data.rebuttal}"</em>`;
    }

    if (coachPoints && data.talking_points) {
      coachPoints.innerHTML = data.talking_points.map(pt => `<li>${pt}</li>`).join('');
    }

    if (coachAction) {
      coachAction.innerHTML = `<strong>Suggested Action:</strong> ${data.action_pitch}`;
    }

    // Store for 1-click note insertion
    window.currentCoachingRebuttal = data.rebuttal;
  } catch (err) {
    console.warn("AI coaching query error:", err);
  }
}

function insertCoachingIntoNotes() {
  const notesField = document.getElementById('call-form-notes');
  if (notesField && window.currentCoachingRebuttal) {
    const prefix = notesField.value.trim() ? notesField.value.trim() + "\n\n" : "";
    notesField.value = prefix + `[AI Objection Coaching Rebuttal Used]:\n"${window.currentCoachingRebuttal}"`;
    notesField.focus();
    const copyBtn = document.getElementById('btnInsertCoachNote');
    if (copyBtn) {
      copyBtn.textContent = 'Inserted into Notes!';
      setTimeout(() => { copyBtn.textContent = '📋 Paste to Notes'; }, 2000);
    }
  }
}

function handleCoachingSpeechInput(val) {
  clearTimeout(coachingDebounceTimer);
  if (!val || val.trim().length < 3) return;
  coachingDebounceTimer = setTimeout(() => {
    triggerObjectionCoach('', val);
  }, 400);
}
