"""
Verification Test Suite for Item 151:
24/7 AI WhatsApp Admissions Concierge Bot for Off-Hours Inquiries
"""

import os
import sys
from datetime import datetime, time, timezone as py_timezone

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.utils import timezone
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory

from accounts.models import User, UserRole
from leads.models import Lead
from activities.models import Activity
from chat.models import Conversation, Message, BusinessAccount
from chat.whatsapp.ai_concierge import (
    is_off_hours,
    classify_admissions_intent,
    generate_concierge_response,
    evaluate_and_respond_concierge
)
from chat.views import AIConciergeSimulateAPI
from chat.whatsapp.webhook import process_incoming_message


def run_tests():
    print("--- [TEST 1: is_off_hours Logic Evaluation] ---")
    # Sunday at 2 PM -> Off-hours
    sunday_2pm = datetime(2026, 11, 8, 14, 0, tzinfo=py_timezone.utc)
    assert is_off_hours(sunday_2pm) == True, "Sunday must be off-hours"

    # Wednesday at 11 PM (23:00) -> Off-hours
    wed_11pm = datetime(2026, 11, 4, 23, 0, tzinfo=py_timezone.utc)
    assert is_off_hours(wed_11pm) == True, "11 PM night must be off-hours"

    # Wednesday at 6 AM -> Off-hours
    wed_6am = datetime(2026, 11, 4, 6, 0, tzinfo=py_timezone.utc)
    assert is_off_hours(wed_6am) == True, "6 AM early morning must be off-hours"

    # Wednesday at 2 PM (14:00) -> Business hours
    wed_2pm = datetime(2026, 11, 4, 14, 0, tzinfo=py_timezone.utc)
    assert is_off_hours(wed_2pm) == False, "Wednesday 2 PM must be within business hours"
    print("PASS: Off-hours evaluation verified across week days and hours.")

    print("\n--- [TEST 2: Intent Classification] ---")
    intents = [
        ("What are the course fees and do you have EMI payment?", "FEES_INSTALLMENTS"),
        ("Please send me the syllabus PDF and course curriculum", "SYLLABUS_COURSE"),
        ("Are there weekend batch timings available for working professionals?", "BATCH_TIMINGS"),
        ("I would like to book a demo counseling appointment with an advisor", "BOOK_APPOINTMENT"),
        ("Hello, good evening!", "GREETING_OR_GENERAL")
    ]
    for text, expected in intents:
        classification = classify_admissions_intent(text)
        assert classification['intent'] == expected, f"Expected {expected} for '{text}', got {classification['intent']}"
        print(f"PASS: Intent '{expected}' correctly detected with confidence {classification['confidence']}.")

    print("\n--- [TEST 3: Auto-Booking & Lead State Update] ---")
    # Setup test counselor & lead
    counselor, _ = User.objects.get_or_create(
        username='test_concierge_counselor',
        defaults={'role': UserRole.COUNSELOR, 'is_on_duty': True, 'email': 'counselor_concierge@example.com'}
    )
    counselor.is_on_duty = True
    counselor.save()

    test_phone = "+919988776655"
    lead, _ = Lead.objects.get_or_create(
        phone="9988776655",
        defaults={'name': 'Simulated Night Lead', 'status': 'New', 'source': 'WhatsApp'}
    )
    lead.status = 'New'
    lead.assigned_counselor = None
    lead.save()

    biz_acc, _ = BusinessAccount.objects.get_or_create(
        phone_number_id="TEST_BIZ_001",
        defaults={'name': 'Main Line', 'phone_number': '+918000000000', 'is_default': True}
    )

    conv, _ = Conversation.objects.get_or_create(
        phone_number=test_phone,
        business_account=biz_acc,
        defaults={'customer_name': 'Simulated Night Lead'}
    )

    # Trigger counseling booking intent in off-hours mode
    result = evaluate_and_respond_concierge(
        conversation=conv,
        text_content="Please schedule a demo session and book an appointment with counselor",
        force_run=True
    )
    assert result is not None, "Concierge must return a response"
    assert result['action_taken'] == 'BOOKED_APPOINTMENT', f"Action should be BOOKED_APPOINTMENT, got {result['action_taken']}"
    assert "Admissions Counseling Session Reserved" in result['reply_text']

    lead.refresh_from_db()
    assert lead.status == 'Demo Scheduled', f"Lead status should update to 'Demo Scheduled', got {lead.status}"
    assert lead.assigned_counselor is not None, "Counselor should be auto-assigned"
    assert lead.center_visit_date is not None, "Follow-up date should be scheduled"

    activity = Activity.objects.filter(object_id=str(lead.id), action='CONCIERGE_DEMO_BOOKED').first()
    assert activity is not None, "Activity timeline entry should be logged"
    print("PASS: Lead successfully scheduled for demo, counselor assigned, and activity logged.")

    print("\n--- [TEST 4: AIConciergeSimulateAPI Endpoint] ---")
    factory = APIRequestFactory()
    req = factory.post('/api/chat/concierge/simulate/', {
        'conversation_id': conv.id,
        'message_text': 'What is the fee for Full Stack Web Development?',
        'force_off_hours': True
    }, format='json')
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin_test', 'admin@example.com', 'pass123')
    req.user = admin_user

    view = AIConciergeSimulateAPI.as_view()
    resp = view(req)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    resp_data = resp.data
    assert resp_data['success'] == True
    assert resp_data['result']['intent'] == 'FEES_INSTALLMENTS'
    assert "Course Fees & No-Cost EMI Options" in resp_data['result']['reply_text']
    print("PASS: AIConciergeSimulateAPI endpoint successfully processed fee inquiry.")

    print("\n--- [TEST 5: Full Inbound Webhook Ingestion Hook] ---")
    # Simulate inbound Meta webhook payload arriving during off-hours
    webhook_payload = {
        'metadata': {
            'phone_number_id': biz_acc.phone_number_id,
            'display_phone_number': biz_acc.phone_number
        },
        'contacts': [
            {'wa_id': '919988776655', 'profile': {'name': 'Simulated Night Lead'}}
        ],
        'messages': [
            {
                'from': '919988776655',
                'id': f'wamid_concierge_{int(timezone.now().timestamp())}',
                'type': 'text',
                'text': {'body': 'What are your weekend batch timings?'},
                'timestamp': str(int(timezone.now().timestamp()))
            }
        ]
    }

    # Temporarily set force active in settings so webhook runs concierge
    from django.conf import settings
    setattr(settings, 'WHATSAPP_AI_CONCIERGE_FORCE_ACTIVE', True)

    initial_msg_count = Message.objects.filter(conversation=conv).count()
    process_incoming_message(webhook_payload, default_business_account=biz_acc)

    # Check that both customer message and outbound concierge bot message were created
    new_messages = Message.objects.filter(conversation=conv).order_by('-id')[:2]
    bot_msg = new_messages[0]
    assert bot_msg.sender == Message.SENDER_AGENT, f"Last message should be from agent/bot, got {bot_msg.sender}"
    assert "Flexible Batch Schedules" in bot_msg.message_text
    print("PASS: Webhook ingestion triggered automatic off-hours concierge reply in conversation.")

    setattr(settings, 'WHATSAPP_AI_CONCIERGE_FORCE_ACTIVE', False)
    print("\nALL 5 TEST SUITES PASSED WITH 100% SUCCESS!")


if __name__ == '__main__':
    run_tests()
