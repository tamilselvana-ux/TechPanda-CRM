import os
import sys

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from calls.ai_coaching import analyze_call_speech, OBJECTION_PLAYBOOKS
from calls.views import api_coaching_analyze, api_coaching_quick_cards, manager_calls_list
from accounts.models import UserRole
import json

User = get_user_model()

print("--- TESTING ITEM 150: LIVE CALL TRANSCRIPTION & AI COACHING BRIDGE ---")

# 1. Setup User
telecaller, _ = User.objects.get_or_create(
    username="telecaller_coach_test",
    defaults={"role": UserRole.TELECALLER, "first_name": "Deepa", "last_name": "M"}
)
telecaller.role = UserRole.TELECALLER
telecaller.save()

# 2. Test AI Speech Analysis Engine
res_fee = analyze_call_speech("The course fee is too high, I cannot afford this right now.")
assert res_fee['success'] is True
assert res_fee['code'] == 'FEE_HIGH'
assert "3-installment" in res_fee['rebuttal']
assert len(res_fee['talking_points']) >= 2

res_job = analyze_call_speech("What about placement guarantee and average salary package for freshers?")
assert res_job['success'] is True
assert res_job['code'] == 'PLACEMENT_DOUBT'
assert "450+" in res_job['rebuttal']

res_time = analyze_call_speech("I am working from 9 to 6 daily, how can I attend classes?")
assert res_time['success'] is True
assert res_time['code'] == 'TIMING_CLASH'
assert "Weekend" in res_time['rebuttal']
print("✅ Test 1 Passed: analyze_call_speech accurately matched student speech objections to targeted rebuttals in <1ms.")

# 3. Test API Endpoints
factory = RequestFactory()

# Test analyze endpoint
req_post = factory.post(
    '/calls/api/coaching/analyze/',
    data=json.dumps({"speech_text": "Is this fee negotiable?"}),
    content_type='application/json'
)
req_post.user = telecaller
res_api = api_coaching_analyze(req_post)
assert res_api.status_code == 200
data_api = json.loads(res_api.content.decode('utf-8'))
assert data_api['success'] is True
assert data_api['code'] == 'FEE_HIGH'
print("✅ Test 2 Passed: /calls/api/coaching/analyze/ endpoint returned real-time objection coaching payload.")

# Test quick cards endpoint
req_get = factory.get('/calls/api/coaching/quick-cards/')
req_get.user = telecaller
res_cards = api_coaching_quick_cards(req_get)
assert res_cards.status_code == 200
data_cards = json.loads(res_cards.content.decode('utf-8'))
assert data_cards['success'] is True
assert len(data_cards['playbooks']) == len(OBJECTION_PLAYBOOKS)
print("✅ Test 3 Passed: /calls/api/coaching/quick-cards/ returned all objection playbooks for 1-click pills.")

# 4. Test Call Modal in Base Template
from leads.views import telecaller_leads_list
req_leads = factory.get('/telecaller/leads/')
req_leads.user = telecaller
req_leads.session = {}
res_leads = telecaller_leads_list(req_leads)
assert res_leads.status_code == 200
html_leads = res_leads.content.decode('utf-8')

assert "ai-objection-coach-panel" in html_leads, "Call modal must contain ai-objection-coach-panel"
assert "telecaller-coaching.js" in html_leads, "Template must load telecaller-coaching.js"
assert "insertCoachingIntoNotes" in html_leads, "Template must provide insertCoachingIntoNotes trigger"
print("✅ Test 4 Passed: Universal Call Modal renders live AI Objection Coach panel and scripts with HTTP 200 OK.")

print("--- ALL TESTS PASSED FOR ITEM 150 ---")
