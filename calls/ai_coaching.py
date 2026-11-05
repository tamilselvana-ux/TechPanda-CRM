import re
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

OBJECTION_PLAYBOOKS = {
    'FEE_HIGH': {
        'category': 'Fee Hesitation',
        'icon': '💰',
        'trigger_keywords': ['fee', 'cost', 'expensive', 'money', 'budget', 'afford', 'discount', 'price', 'rupees'],
        'rebuttal': "I completely understand budget is important! Did you know we offer a flexible 3-installment split payment plan starting at just ₹15,000 down payment? Plus, we have an initial 7-day unconditional money-back guarantee.",
        'talking_points': [
            "Flexible 3-month split installment plan (0% interest).",
            "Initial down payment as low as ₹15,000 to reserve seat.",
            "Includes all course material, cloud labs, and placement certification."
        ],
        'action_pitch': "Offer Split Payment Plan & Reserve Seat with Token"
    },
    'PLACEMENT_DOUBT': {
        'category': 'Job & Placement Guarantee',
        'icon': '💼',
        'trigger_keywords': ['placement', 'job', 'salary', 'hiring', 'package', 'company', 'interview', 'fresher', 'career'],
        'rebuttal': "Great question! iTechPanda Academy has 450+ active hiring partners including Zoho, TCS, and top tier tech startups. We provide dedicated 1:1 resume optimization, mock technical interviews, and unlimited placement drives until you are placed.",
        'talking_points': [
            "450+ partnered tech companies across Chennai & Bangalore.",
            "Dedicated placement manager conducts weekly mock technical rounds.",
            "Average alumni salary package is 4.8 LPA to 8.5 LPA."
        ],
        'action_pitch': "Share Recent Placement Alumni PDF & Offer Mock Interview Demo"
    },
    'TIMING_CLASH': {
        'category': 'Schedule / Working Professional',
        'icon': '⏰',
        'trigger_keywords': ['timing', 'schedule', 'working', 'office', 'shift', 'college', 'time', 'hours', 'weekend', 'busy'],
        'rebuttal': "We completely accommodate working professionals and college students! We run special Weekend Batches (Sat/Sun 10 AM - 2 PM) as well as Early Morning and Evening 8 PM slots. Every live session is recorded and uploaded to your 24/7 LMS portal.",
        'talking_points': [
            "Weekend batches exclusively designed for working professionals.",
            "All live sessions recorded in HD with lifetime LMS portal access.",
            "Flexible batch-switch option if your work shift changes."
        ],
        'action_pitch': "Register for Weekend Professional Batch Slot"
    },
    'COMPETITOR_COMPARISON': {
        'category': 'Comparing Other Institutes',
        'icon': '🆚',
        'trigger_keywords': ['other', 'besant', 'jspider', 'online', 'coursera', 'udemy', 'compare', 'better'],
        'rebuttal': "While recorded video courses teach theoretical basics, iTechPanda is 100% project-driven. You build 4 live production capstone applications from scratch with senior engineering mentors reviewing your code line-by-line in git.",
        'talking_points': [
            "100% hands-on coding labs; no passive recorded slides.",
            "Direct 1:1 mentorship with real tech leads from industry.",
            "Live in-center doubt clarification cabins in Anna Nagar & Velachery."
        ],
        'action_pitch': "Invite for Free 1-on-1 In-Cabin Code Review Session"
    },
    'NOT_SURE': {
        'category': 'Unsure / Indecisive',
        'icon': '🤷',
        'trigger_keywords': ['not sure', 'confused', 'later', 'think', 'discuss', 'parents', 'call back', 'undecided'],
        'rebuttal': "That is completely natural! To help you see if this career path is the right fit, why don't you attend our Free 2-Hour Hands-on Demo Class this Saturday? There is zero payment needed, and you can experience the mentors and curriculum directly.",
        'talking_points': [
            "Zero cost, zero obligation 2-hour Live Demo Class.",
            "Sit in an actual class, meet the mentor, and evaluate the teaching.",
            "Parents / guardians are very welcome to join the orientation."
        ],
        'action_pitch': "Book Free Saturday Interactive Demo Slot"
    }
}


def analyze_call_speech(speech_text, manual_category=None):
    """
    Sub-second real-time AI Objection Coaching engine.
    Analyzes student utterance or selected objection category and returns
    targeted rebuttal, talking points, and action pitch.
    """
    if manual_category and manual_category in OBJECTION_PLAYBOOKS:
        return {
            'success': True,
            'code': manual_category,
            **OBJECTION_PLAYBOOKS[manual_category]
        }

    text_lower = (speech_text or '').lower()
    best_match = None
    max_score = 0

    for code, playbook in OBJECTION_PLAYBOOKS.items():
        score = sum(1 for kw in playbook['trigger_keywords'] if kw in text_lower)
        if score > max_score:
            max_score = score
            best_match = code

    # Fallback default if speech is generic
    if not best_match or max_score == 0:
        best_match = 'NOT_SURE'

    return {
        'success': True,
        'code': best_match,
        'detected_from_keywords': max_score > 0,
        **OBJECTION_PLAYBOOKS[best_match]
    }
