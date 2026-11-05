"""
24/7 AI WhatsApp Admissions Concierge Bot for Off-Hours Inquiries.
Provides automated, sub-second responses for prospective student inquiries outside normal office hours:
- Course Fees & No-Cost EMI Installment breakdowns
- Syllabus, Curriculum Highlights & Course Kit Brochure dispatch
- Batch Schedules & Working Professional Weekend Slots
- 1-Click Counselor Appointment & Live Demo Booking on Academic Calendar
"""

import logging
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

# Business Hours in IST (Mon-Sat 09:00 to 19:30)
BUSINESS_HOUR_START = time(9, 0)
BUSINESS_HOUR_END = time(19, 30)


def is_off_hours(check_dt: Optional[datetime] = None, force_override: Optional[bool] = None) -> bool:
    """
    Determines whether the given or current timestamp falls outside official business hours.
    Business Hours: Monday to Saturday, 09:00 AM to 7:30 PM (IST / Local time).
    Off-hours: Sunday all day, or any day before 09:00 AM or after 7:30 PM.
    """
    if force_override is not None:
        return bool(force_override)

    if getattr(settings, 'WHATSAPP_AI_CONCIERGE_FORCE_ACTIVE', False):
        return True

    now = check_dt or timezone.localtime()

    # Sunday is index 6 in Python weekday() (0=Mon, 6=Sun)
    if now.weekday() == 6:
        return True

    current_t = now.time()
    if current_t < BUSINESS_HOUR_START or current_t >= BUSINESS_HOUR_END:
        return True

    return False


def classify_admissions_intent(text: str) -> Dict[str, Any]:
    """
    Analyzes student message text and maps to core admissions intents:
    - FEES_INSTALLMENTS
    - SYLLABUS_COURSE
    - BATCH_TIMINGS
    - BOOK_APPOINTMENT
    - GREETING_OR_GENERAL
    Uses regex word boundaries to avoid false positives.
    """
    import re
    text_lower = (text or '').lower().strip()

    # Normalize pure greetings like 'good morning' or 'good evening' so they don't trip batch timing
    text_clean_timing = re.sub(r'good\s*(morning|evening|afternoon|day)', '', text_lower)

    appointment_triggers = [
        r'\bdemo\b', r'\bbook\b', r'\bcounselor\b', r'\bcounselling\b', r'\bcounseling\b',
        r'\bappointment\b', r'\bvisit\b', r'call\s*me', r'call\s*back', r'\badmissions\b',
        r'\bseat\b', r'\bmeet\b', r'schedule\s*demo', r'talk\s*to\s*advisor'
    ]

    fee_triggers = [
        r'\bfee\b', r'\bfees\b', r'\bcost\b', r'\bprice\b', r'\bpricing\b',
        r'\bcharge\b', r'\bcharges\b', r'\bemi\b', r'installment', r'instalment',
        r'\bpay\b', r'\bpayment\b', r'\bscholarship\b', r'\bdiscount\b', r'down\s*payment'
    ]

    timing_triggers = [
        r'\btiming', r'\btimings\b', r'\btime\b', r'\bbatch', r'\bschedule',
        r'\bweekend\b', r'\bweekday\b', r'\bmorning\b', r'\bevening\b', r'\bslot',
        r'\bhours\b', r'\bduration\b', r'how\s*long'
    ]

    syllabus_triggers = [
        r'\bsyllabus\b', r'\bcurriculum\b', r'\btopics\b', r'\bmodule', r'\bbrochure\b',
        r'\bpdf\b', r'\bcatalog', r'what\s*will\s*i\s*learn', r'course\s*content',
        r'full\s*stack', r'\bpython\b', r'\bmern\b', r'data\s*science', r'\bai\b', r'digital\s*marketing'
    ]

    if any(re.search(pat, text_lower) for pat in appointment_triggers):
        return {
            'intent': 'BOOK_APPOINTMENT',
            'confidence': 0.95,
            'summary': 'Student requested counselor call or demo booking'
        }

    if any(re.search(pat, text_lower) for pat in fee_triggers):
        return {
            'intent': 'FEES_INSTALLMENTS',
            'confidence': 0.92,
            'summary': 'Inquiry regarding course fees, EMI or installment plans'
        }

    if any(re.search(pat, text_clean_timing) for pat in timing_triggers):
        return {
            'intent': 'BATCH_TIMINGS',
            'confidence': 0.88,
            'summary': 'Inquiry regarding batch timings and class schedules'
        }

    if any(re.search(pat, text_lower) for pat in syllabus_triggers):
        return {
            'intent': 'SYLLABUS_COURSE',
            'confidence': 0.90,
            'summary': 'Inquiry regarding course syllabus, modules or brochure'
        }

    return {
        'intent': 'GREETING_OR_GENERAL',
        'confidence': 0.75,
        'summary': 'General greeting or off-hours introductory inquiry'
    }


def generate_concierge_response(intent_data: Dict[str, Any], conversation, lead=None) -> Dict[str, Any]:
    """
    Constructs the appropriate high-touch admissions response and executes actions
    (such as automated appointment booking on lead timeline).
    """
    intent = intent_data.get('intent', 'GREETING_OR_GENERAL')
    phone = getattr(conversation, 'phone_number', '')
    customer_name = getattr(conversation, 'customer_name', 'Student')
    if customer_name == phone:
        customer_name = "there"

    action_taken = "NONE"
    appointment_info = {}

    if intent == 'BOOK_APPOINTMENT':
        # Automatically book priority counseling appointment on Lead record
        action_taken = "BOOKED_APPOINTMENT"
        counselor_name = "Senior Academic Advisor"

        if lead:
            try:
                from accounts.models import User, UserRole
                from activities.models import Activity

                # Locate on-duty counselor or branch counselor
                counselor = None
                if getattr(lead, 'branch', None):
                    counselor = User.objects.filter(
                        role=UserRole.COUNSELOR,
                        branch=lead.branch,
                        is_active=True,
                        is_on_duty=True
                    ).first()

                if not counselor:
                    counselor = User.objects.filter(
                        role=UserRole.COUNSELOR,
                        is_active=True,
                        is_on_duty=True
                    ).first() or User.objects.filter(
                        role=UserRole.COUNSELOR,
                        is_active=True
                    ).first()

                if counselor:
                    counselor_name = counselor.get_full_name() or counselor.username
                    if not lead.assigned_counselor:
                        lead.assigned_counselor = counselor

                # Transition lead status to Demo Scheduled
                lead.status = 'Demo Scheduled'
                tomorrow_morning = timezone.now() + timedelta(days=1)
                lead.center_visit_date = tomorrow_morning
                lead.save(update_fields=['status', 'assigned_counselor', 'center_visit_date', 'updated_at'])

                try:
                    from followups.models import FollowUp
                    FollowUp.objects.create(
                        lead=lead,
                        assigned_user=counselor,
                        follow_up_date=tomorrow_morning.date(),
                        follow_up_time=time(10, 30),
                        status='PENDING',
                        notes='24/7 AI Concierge: Priority admissions counseling demo scheduled'
                    )
                except Exception as fu_err:
                    logger.warning(f"FollowUp creation error: {fu_err}")

                # Log activity on lead timeline
                Activity.objects.create(
                    user=counselor or User.objects.filter(is_superuser=True).first(),
                    action='CONCIERGE_DEMO_BOOKED',
                    description=f"24/7 AI Admissions Concierge priority-booked counseling slot for {phone} with {counselor_name}.",
                    object_type='Lead',
                    object_id=str(lead.id)
                )

                appointment_info = {
                    'counselor': counselor_name,
                    'status': 'Demo Scheduled',
                    'scheduled_time': 'Tomorrow at 10:30 AM'
                }
            except Exception as e:
                logger.error(f"Error booking concierge appointment for lead {lead.id}: {e}", exc_info=True)

        reply_text = (
            f"✅ *Admissions Counseling Session Reserved!*\n\n"
            f"Hello {customer_name}! I have priority-booked your 1-on-1 counseling session with our {counselor_name} for tomorrow at *10:30 AM*.\n\n"
            f"📞 *Call Details*: Our advisor will contact you on this number ({phone}).\n"
            f"📍 *Option*: Would you prefer this session via Google Meet video call, or an in-person visit to our nearest iTechPanda branch?\n\n"
            f"Reply *'Meet'* or *'Campus'* to let us know!"
        )

    elif intent == 'FEES_INSTALLMENTS':
        reply_text = (
            f"🎓 *iTechPanda Academy — Course Fees & No-Cost EMI Options*\n\n"
            f"Hello {customer_name}! Here is our transparent fee structure for our flagship certification programs:\n\n"
            f"• *Full Stack Software Engineering (MERN / Django)*: ₹42,000 (Early scholarship up to ₹10,000 available)\n"
            f"• *Data Science & Applied AI / ML*: ₹48,000\n"
            f"• *Digital Marketing & Performance Growth*: ₹32,000\n\n"
            f"💳 *Flexible Installments*:\n"
            f"All courses can be split into 2 or 3 equal monthly installments with zero interest and official GST invoice.\n\n"
            f"Would you like to book a 1-on-1 counselor call tomorrow morning to check your scholarship eligibility? Reply *'Book'* or *'Syllabus'*!"
        )

    elif intent == 'SYLLABUS_COURSE':
        action_taken = "SENT_BROCHURE"
        brochure_url = "https://itechpanda.com/static/brochures/itechpanda_course_catalog.pdf"
        reply_text = (
            f"📚 *iTechPanda Academy — Course Curriculum & Project Roadmap*\n\n"
            f"Hello {customer_name}! Our curriculum is designed with 100% live production projects:\n\n"
            f"• *Phase 1*: Fundamentals, Clean Code & Data Structures\n"
            f"• *Phase 2*: Full-Stack Web Architecture & REST / GraphQL APIs\n"
            f"• *Phase 3*: Database Design, Cloud Deployment & Security\n"
            f"• *Phase 4*: Mock Technical Interviews & Direct Placement Drives\n\n"
            f"📥 Download the full PDF course catalog:\n{brochure_url}\n\n"
            f"Reply *'Demo'* to reserve a seat in our upcoming live mentor session!"
        )

    elif intent == 'BATCH_TIMINGS':
        reply_text = (
            f"⏰ *iTechPanda Academy — Flexible Batch Schedules*\n\n"
            f"Hello {customer_name}! We offer both weekday and working professional batches:\n\n"
            f"• *Morning Fast-Track*: 8:00 AM – 10:00 AM (Mon–Fri)\n"
            f"• *Regular Day Immersion*: 10:30 AM – 1:30 PM (Mon–Fri)\n"
            f"• *Evening Career Transition*: 6:00 PM – 8:00 PM (Mon–Fri)\n"
            f"• *Weekend Professional Batch*: 10:00 AM – 2:00 PM (Sat & Sun)\n\n"
            f"All batches feature live interactive lectures + lifetime access to HD class recordings.\n\n"
            f"Which timing fits your routine best? Reply with your preferred slot!"
        )

    else:
        reply_text = (
            f"👋 *Welcome to iTechPanda Academy!* 🐼\n\n"
            f"Our live admissions desk is currently closed for the night (Office Hours: Mon–Sat 9:00 AM – 7:30 PM), but I am your **24/7 AI Admissions Concierge**.\n\n"
            f"How can I assist you right away?\n"
            f"1️⃣ *Fees & No-Cost EMI* — Reply *'Fees'*\n"
            f"2️⃣ *Course Curriculum & Syllabus* — Reply *'Syllabus'*\n"
            f"3️⃣ *Batch Timings & Schedules* — Reply *'Timings'*\n"
            f"4️⃣ *Book Counselor Call / Demo* — Reply *'Book'*\n\n"
            f"Type any question and I'll help you immediately!"
        )

    return {
        'reply_text': reply_text,
        'action_taken': action_taken,
        'intent': intent,
        'appointment_info': appointment_info
    }


def evaluate_and_respond_concierge(
    conversation,
    incoming_message=None,
    text_content: str = "",
    force_run: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Main evaluation pipeline called upon receiving an inbound WhatsApp message.
    Checks for off-hours condition, classifies intent, generates response,
    persists the bot message, and broadcasts live to channels.
    """
    from chat.models import Message

    # Check if incoming message is from a customer
    if incoming_message and getattr(incoming_message, 'sender', '') != Message.SENDER_CUSTOMER:
        return None

    # Verify off-hours or forced test mode
    if not is_off_hours(force_override=force_run if force_run else None):
        return None

    # Find associated CRM Lead
    lead = None
    try:
        from leads.models import Lead
        from chat.whatsapp.webhook import format_phone_e164
        phone_digits = ''.join(c for c in conversation.phone_number if c.isdigit())[-10:]
        lead = Lead.objects.filter(phone__endswith=phone_digits).first()
    except Exception as lead_err:
        logger.warning(f"Could not link lead for concierge response: {lead_err}")

    # Classify intent & generate structured response
    intent_data = classify_admissions_intent(text_content)
    result = generate_concierge_response(intent_data, conversation, lead=lead)
    reply_text = result['reply_text']

    # Persist outbound bot message
    now = timezone.now()
    bot_message = Message.objects.create(
        conversation=conversation,
        sender=Message.SENDER_AGENT,
        message_type=Message.TYPE_TEXT,
        message_text=reply_text,
        status=Message.STATUS_DELIVERED,
        timestamp=now
    )

    # Update conversation state
    conversation.last_message = reply_text[:120] + ('...' if len(reply_text) > 120 else '')
    conversation.last_message_time = now
    conversation.save(update_fields=['last_message', 'last_message_time', 'updated_at'])

    # Safely broadcast to Django Channels
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"chat_{conversation.id}",
                {
                    "type": "chat_message",
                    "message": {
                        "id": bot_message.id,
                        "conversation_id": conversation.id,
                        "sender": bot_message.sender,
                        "message_type": bot_message.message_type,
                        "message_text": bot_message.message_text,
                        "media_url": None,
                        "whatsapp_message_id": "",
                        "status": bot_message.status,
                        "timestamp": bot_message.timestamp.isoformat(),
                        "display_time": bot_message.display_time,
                    }
                }
            )
            async_to_sync(channel_layer.group_send)(
                "inbox_updates",
                {
                    "type": "conversation_update",
                    "conversation": {
                        "id": conversation.id,
                        "business_account_id": conversation.business_account_id,
                        "customer_name": conversation.customer_name,
                        "phone_number": conversation.phone_number,
                        "last_message": conversation.last_message,
                        "last_message_time": conversation.display_time,
                        "unread_count": conversation.unread_count,
                    }
                }
            )
    except Exception as ch_err:
        logger.warning(f"Concierge channel broadcast failed: {ch_err}")

    # Attempt WhatsApp Cloud API transmission if live
    try:
        from chat.whatsapp.messages import send_text_message
        send_text_message(
            to_phone_number=conversation.phone_number,
            text=reply_text,
            business_account=conversation.business_account
        )
    except Exception as wa_api_err:
        logger.info(f"WhatsApp Cloud API simulated/unconfigured dispatch: {wa_api_err}")

    return {
        'reply_text': reply_text,
        'action_taken': result['action_taken'],
        'intent': result['intent'],
        'appointment_info': result.get('appointment_info', {}),
        'bot_message_id': bot_message.id
    }
