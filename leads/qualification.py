from django.utils.html import escape
from django.utils.safestring import mark_safe
"""
Universal Inbound Lead Qualification Normalizer & Auto-fill Service.
Automatically extracts, normalizes, and maps inbound lead answers from
Facebook Lead Ads, WhatsApp Chat flows, Google Sheets, and Walk-in forms
into structured Lead Qualification fields, custom_fields JSON, and CRM records.
"""
import re
import logging
from typing import Dict, Any, Tuple, Optional

from products.models import Product
from branches.models import Branch

log = logging.getLogger('crm')

# Canonical in-call qualification field keys
QUALIFICATION_FIELDS = {
    'degree',
    'passed_out',
    'working_status',
    'designation',
    'join_preference',
    'lead_source',
    'location',
    'purpose',
    'total_experience',
    'courses',
    'pref_branch',
    'pref_exam_loc',
    'college',
    'current_ctc',
    'expected_ctc',
    'retargeted',
}

# Synonym aliases mapping inbound question keys to canonical qualification keys
QUESTION_ALIASES = {
    'degree': [
        'degree', 'qualification', 'education', 'highest qualification',
        'course completed', 'educational qualification', 'study', 'major'
    ],
    'passed_out': [
        'passedout', 'passed out', 'year of pass', 'passing year', 'yop',
        'year of passing', 'graduation year', 'passout year', 'batch year'
    ],
    'working_status': [
        'working status', 'employment status', 'working', 'job status',
        'status of work', 'what best describes you',
        'current status', 'employment', 'are you currently working',
        'are you working or student', 'profession', 'occupation',
        'what describes you best'
    ],
    'designation': [
        'designation', 'role', 'current role', 'job title', 'current designation',
        'position', 'current position'
    ],
    'join_preference': [
        'class mode', 'class_mode', 'demo class', 'demo', 'how would you like to join the course', 'joining preference', 'mode',
        'course mode', 'batch mode', 'prefer learning mode',
        'preferred mode', 'learning mode', 'which batch would you prefer',
        'batch preference', 'training mode', 'preferred batch',
        'mode of training', 'timing', 'batch'
    ],
    'lead_source': [
        'lead source', 'source', 'lead source 1', 'how did you hear about us',
        'referral source'
    ],
    'location': [
        'location', 'city', 'native', 'address', 'current city', 'town',
        'residing city', 'place', 'state'
    ],
    'purpose': [
        'purpose', 'objective', 'reason', 'intent', 'why do you want to learn',
        'goal', 'learning goal'
    ],
    'total_experience': [
        'total experience', 'experience', 'exp', 'work experience',
        'years of experience', 'total exp'
    ],
    'courses': [
        'courses', 'course', 'domain', 'subject', 'interested course',
        'program', 'programme', 'which course are you looking for',
        'interested in', 'selected course'
    ],
    'pref_branch': [
        'preferred branch', 'pref branch', 'branch location', 'nearest branch',
        'preferred center', 'center'
    ],
    'pref_exam_loc': [
        'preferred exam location', 'exam location', 'exam city', 'pref exam loc'
    ],
    'college': [
        'college', 'university', 'institution', 'college name', 'school name',
        'institute', 'university/college'
    ],
    'current_ctc': [
        'current ctc', 'ctc', 'current salary', 'salary', 'present salary',
        'annual salary', 'present ctc'
    ],
    'expected_ctc': [
        'expected ctc', 'exp ctc', 'expected salary', 'future ctc'
    ],
    'retargeted': [
        'retargeted', 'retarget', 're-target', 'is retargeted'
    ]
}


def _clean_str(s: str) -> str:
    s = str(s or '').lower().replace('_', ' ').replace('-', ' ')
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return ' '.join(s.split())


# Reverse lookup dictionary: clean lowercase question alias -> canonical field key
_ALIAS_TO_CANONICAL = {}
for canonical, aliases in QUESTION_ALIASES.items():
    _ALIAS_TO_CANONICAL[_clean_str(canonical)] = canonical
    for a in aliases:
        _ALIAS_TO_CANONICAL[_clean_str(a)] = canonical


def match_canonical_field(raw_key: str) -> Optional[str]:
    """
    Finds the canonical qualification field name for any raw inbound question/key.
    Supports exact matching, alias matching, and substring keyword matching.
    """
    if not raw_key:
        return None
    k_clean = _clean_str(raw_key)

    # 1. Exact match in aliases
    if k_clean in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[k_clean]

    # 2. Substring matching
    for alias_clean, canonical in _ALIAS_TO_CANONICAL.items():
        if len(alias_clean) >= 4 and (alias_clean in k_clean or k_clean in alias_clean):
            return canonical

    return None


def extract_course_from_text(text: str) -> Optional[str]:
    """
    Extracts a likely course/program name from campaign, ad, or form strings.
    E.g. 'DP | Leads | Digital Marketing Course | Oct 06 2026 ad' -> 'Digital Marketing Course'
    """
    if not text:
        return None
    tokens = re.split(r'[|\-:]', str(text))
    for tok in tokens:
        tok_clean = tok.strip()
        if any(w in tok_clean.lower() for w in (
            'course', 'program', 'training', 'marketing', 'python', 'java',
            'data science', 'full stack', 'devops', 'aws', 'cloud', 'ai', 'analytics'
        )):
            cleaned = re.sub(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{4}\b', '', tok_clean, flags=re.I).strip()
            cleaned = re.sub(r'\b(ad|leads|lead|campaign)\b', '', cleaned, flags=re.I).strip()
            if cleaned and len(cleaned) > 2:
                return cleaned
    return None


def normalize_value(canonical_key: str, raw_value: Any) -> Tuple[str, Optional[Tuple[str, str]]]:
    """
    Normalizes raw inbound text into CRM dropdown choices.
    Returns (normalized_value, secondary_field_assignment).
    Example: 'career_switcher' -> ('Working professional', ('purpose', 'Career Transition'))
    """
    if raw_value is None:
        return '', None

    val_str = str(raw_value).strip()
    if not val_str or val_str.lower() in ('null', 'none', 'n/a', 'na', 'empty'):
        return '', None

    v_clean = val_str.lower().replace('-', '_').replace(' ', '_').strip()
    secondary_attr = None

    if canonical_key == 'join_preference':
        # Options: ['Online', 'Classroom', 'Hybrid', 'Weekend Batch', 'Weekday Batch']
        if 'demo' in v_clean:
            val_str = 'Demo Class'
        elif any(w in v_clean for w in ('classroom', 'offline', 'in_person', 'walk_in', 'center')):
            val_str = 'Classroom'
        elif any(w in v_clean for w in ('online', 'zoom', 'virtual', 'remote', 'live_online')):
            val_str = 'Online'
        elif 'hybrid' in v_clean or 'both' in v_clean:
            val_str = 'Hybrid'
        elif any(w in v_clean for w in ('weekend', 'saturday', 'sunday')):
            val_str = 'Weekend Batch'
        elif any(w in v_clean for w in ('weekday', 'daily', 'regular', 'mon_fri')):
            val_str = 'Weekday Batch'

    elif canonical_key == 'working_status':
        # Options: ['Working professional', 'Student', 'Looking for job', 'Fresher', 'Career Gap', 'Freelancer', 'Other']
        if any(w in v_clean for w in ('career_switcher', 'career_change', 'switcher', 'transition')):
            val_str = 'Working professional'
            secondary_attr = ('purpose', 'Career Transition')
        elif any(w in v_clean for w in ('student', 'college', 'studying', 'final_year')):
            val_str = 'Student'
        elif any(w in v_clean for w in ('working', 'employed', 'employee', 'professional', 'salaried')):
            val_str = 'Working professional'
        elif any(w in v_clean for w in ('looking_for_job', 'job_seeker', 'jobseeker', 'unemployed', 'searching')):
            val_str = 'Looking for job'
        elif any(w in v_clean for w in ('fresher', 'recent_grad', 'new_grad', 'passed_out')):
            val_str = 'Fresher'
        elif any(w in v_clean for w in ('gap', 'break', 'career_gap')):
            val_str = 'Career Gap'
        elif any(w in v_clean for w in ('freelancer', 'self_employed', 'business')):
            val_str = 'Freelancer'

    elif canonical_key == 'purpose':
        # Options: ['Career Transition', 'Upskilling', 'Placement Assistance', 'Higher Studies', 'Certification', 'Interview Preparation', 'Other']
        if any(w in v_clean for w in ('career_switcher', 'transition', 'switch', 'career_change')):
            val_str = 'Career Transition'
        elif any(w in v_clean for w in ('upskill', 'knowledge', 'skill', 'learn')):
            val_str = 'Upskilling'
        elif any(w in v_clean for w in ('placement', 'job', 'interview', 'career')):
            val_str = 'Placement Assistance'
        elif any(w in v_clean for w in ('higher_studies', 'ms', 'masters', 'abroad')):
            val_str = 'Higher Studies'
        elif any(w in v_clean for w in ('certif', 'diploma')):
            val_str = 'Certification'

    elif canonical_key == 'passed_out':
        match = re.search(r'\b(19\d\d|20\d\d)\b', val_str)
        if match:
            year_int = int(match.group(1))
            if 1970 <= year_int <= 2040:
                val_str = str(year_int)

    elif canonical_key == 'location':
        parts = [p.capitalize() for p in val_str.replace('_', ' ').split()]
        val_str = " ".join(parts)

    elif canonical_key in ('degree', 'college', 'designation'):
        if '_' in val_str:
            val_str = val_str.replace('_', ' ').title()

    return val_str, secondary_attr


def normalize_inbound_payload(data: Dict[str, Any], source: str = '') -> Dict[str, Any]:
    """
    Parses a raw key-value dictionary (from Facebook, WhatsApp, or Google Sheets)
    into a structured qualification mapping.
    """
    if not isinstance(data, dict):
        return {'attributes': {}, 'origins': {}, 'product_suggestion': None, 'branch_suggestion': None}

    attributes = {}
    origins = {}
    product_suggestion = None
    branch_suggestion = None

    skip_keys = {
        'full_name', 'name', 'first_name', 'last_name',
        'phone', 'phone_number', 'alternate_phone', 'email', 'email_address',
        'inbox_url', 'id', 'lead_id', 'provider_event_id', 'created_time',
        '_crm_synced'
    }

    # First check ad/campaign/form names for course extraction
    for metadata_key in ('ad_name', 'campaign_name', 'form_name'):
        meta_val = data.get(metadata_key)
        if meta_val and not product_suggestion:
            ext = extract_course_from_text(meta_val)
            if ext:
                product_suggestion = ext

    for raw_k, raw_v in data.items():
        k_str = str(raw_k).strip()
        if not k_str or k_str.startswith('_') or k_str.lower() in skip_keys:
            continue

        # Check for Course / Product suggestion
        if any(w in k_str.lower() for w in ('course', 'program', 'subject', 'domain')):
            if raw_v and str(raw_v).strip():
                product_suggestion = str(raw_v).strip()

        # Check for Branch / Center suggestion
        if any(w in k_str.lower() for w in ('branch', 'center', 'preferred_branch')):
            if raw_v and str(raw_v).strip():
                branch_suggestion = str(raw_v).strip()

        canonical = match_canonical_field(k_str)
        if canonical:
            val, secondary = normalize_value(canonical, raw_v)
            if val and canonical not in attributes:
                attributes[canonical] = val
                origins[canonical] = source or 'Inbound'
            if secondary:
                sec_key, sec_val = secondary
                if sec_val and sec_key not in attributes:
                    attributes[sec_key] = sec_val
                    origins[sec_key] = source or 'Inbound'

    return {
        'attributes': attributes,
        'origins': origins,
        'product_suggestion': product_suggestion,
        'branch_suggestion': branch_suggestion,
    }


def autofill_lead_qualification(
    lead,
    raw_payload: Dict[str, Any],
    source: str = 'Inbound',
    preserve_manual_edits: bool = True
) -> Dict[str, Any]:
    """
    Applies normalized qualification fields to a Lead instance.
    - Updates lead.custom_fields safely without overwriting human-filled data.
    - Sets lead.product if unassigned and matched (or stores in custom_fields).
    - Sets lead.branch if unassigned and matched.
    - Appends structured notes attributes.
    Returns dictionary of applied fields.
    """
    if not lead or not raw_payload:
        return {}

    parsed = normalize_inbound_payload(raw_payload, source=source)
    attributes = parsed['attributes']
    origins = parsed['origins']

    cf = dict(lead.custom_fields or {})
    field_origins = dict(cf.get('_field_origins') or {})

    applied = {}
    updated_fields = set()

    for key, val in attributes.items():
        existing_val = cf.get(key)
        if preserve_manual_edits and existing_val and str(existing_val).strip() not in ('', 'Empty'):
            continue

        cf[key] = val
        field_origins[key] = origins.get(key, source)
        applied[key] = val

    # Resolve product if lead has no product
    prod_candidate = parsed.get('product_suggestion') or attributes.get('courses')
    if prod_candidate:
        if not lead.product_id:
            matched_prod = (
                Product.objects.filter(name__iexact=prod_candidate, status='Active').first()
                or Product.objects.filter(name__icontains=prod_candidate, status='Active').first()
            )
            if matched_prod:
                lead.product = matched_prod
                updated_fields.add('product')
                applied['courses'] = matched_prod.name
            else:
                if 'courses' not in cf or not cf['courses']:
                    cf['courses'] = prod_candidate
                    field_origins['courses'] = origins.get('courses', source)
                    applied['courses'] = prod_candidate

    # Resolve branch if lead has no branch
    if not lead.branch_id:
        branch_candidate = parsed.get('branch_suggestion') or attributes.get('pref_branch') or attributes.get('location')
        if branch_candidate:
            matched_branch = (
                Branch.objects.filter(name__iexact=branch_candidate, status='Active').first()
                or Branch.objects.filter(name__icontains=branch_candidate, status='Active').first()
            )
            if matched_branch:
                lead.branch = matched_branch
                updated_fields.add('branch')
                applied['branch'] = matched_branch.name

    if applied or ('_field_origins' not in cf and field_origins):
        cf['_field_origins'] = field_origins
        lead.custom_fields = cf
        updated_fields.add('custom_fields')

    # Synchronize structured attributes into notes format (pipes) for legacy compatibility
    if applied:
        from .detail_service import update_lead_notes_attribute
        current_notes = lead.notes or ''
        for k, v in applied.items():
            if k in QUALIFICATION_FIELDS:
                current_notes = update_lead_notes_attribute(current_notes, k, v)
        if current_notes != lead.notes:
            lead.notes = current_notes
            updated_fields.add('notes')

    if updated_fields:
        lead.save(update_fields=list(updated_fields) + ['updated_at'])
        log.info("Autofilled lead #%s qualification from %s: %s", lead.id, source, list(applied.keys()))

    return applied


STATUS_CALL_OBJECTIVES = {
    'New': 'Verify career goals and course interest, assess student background, and invite for a live free Demo session or Campus Visit.',
    'Contacted': 'Follow up on introductory interest, confirm learning mode (Online vs Classroom), and book a Demo session.',
    'Interested': 'Deep-dive into curriculum modules and hands-on capstone projects, discuss batch timings, and schedule a Demo.',
    'Discussion': 'Address syllabus and schedule inquiries, answer career transition questions, and present clear next steps.',
    'Follow-up': 'Review previous discussion notes, answer pending queries, and secure confirmed registration or campus visit.',
    'Demo Scheduled': 'Re-confirm attendance for upcoming Demo session, provide meeting/center link, and prepare instructor.',
    'Institute Visit': 'Confirm visit time, share branch address and directions, and ensure course counselor is assigned for walkthrough.',
    'Visit Scheduled': 'Confirm visit time, share branch address and directions, and ensure course counselor is assigned for walkthrough.',
    'Visited': 'Follow up on campus visit experience, clarify questions, and present GST-inclusive fee structure with installment options.',
    'Counseling': 'Address syllabus or certification doubts, review flexible installment plan, and guide enrollment.',
    'Converted': 'Warm welcome, confirm batch starting date, issue official GST tax invoice, and verify batch onboarding.',
    'Enrolled': 'Warm welcome, confirm batch starting date, issue official GST tax invoice, and verify batch onboarding.',
    'Joined': 'Verify student portal onboarding, course material access, and first week mentor touchpoint.',
    'No Answer': 'Send polite WhatsApp/SMS course overview and set a scheduled callback attempt for afternoon/evening.',
    'Busy': 'Respect current call constraint, send syllabus on WhatsApp, and schedule precise callback time.',
    'Switched Off': 'Log unreachable status, trigger automated WhatsApp introduction, and retry next business day morning.',
    'Later': 'Check updated career timeline, share recent placement outcomes, and present upcoming batch intake dates.',
    'Lost': 'Record primary reason for drop-off, archive gracefully, and offer self-paced webinar resources.',
    'Not Interested': 'Politely record feedback, ensure no spam frequency, and archive record cleanly.',
    'Not Joined': 'Understand timing/budget constraints and offer flexible weekend or upcoming batch slots.',
}


def _format_rel_time(dt):
    if not dt:
        return 'Empty'
    from django.utils import timezone
    diff = timezone.now() - dt
    secs = int(diff.total_seconds())
    if secs < 60:
        return 'Just now'
    elif secs < 3600:
        m = secs // 60
        return f'{m}m ago'
    elif secs < 86400:
        h = secs // 3600
        return f'{h}h ago'
    elif secs < 604800:
        d = secs // 86400
        return f'{d}d ago'
    return dt.strftime('%d %b')


def generate_smart_precall_pitch(lead) -> str:
    cf = lead.custom_fields or {}
    
    name = lead.name or 'The lead'
    status = cf.get('working_status') or ''
    purpose = cf.get('purpose') or ''
    mode = cf.get('join_preference') or ''
    loc = cf.get('location') or (lead.branch.name if lead.branch else '')
    course = lead.product.name if lead.product else cf.get('courses', '')

    if purpose and purpose not in ('Other', 'Empty'):
        persona = purpose
    elif status and status not in ('Other', 'Empty'):
        persona = status
    else:
        persona = ''

    safe_name = escape(name)
    safe_persona = escape(persona)
    safe_mode = escape(mode)
    safe_course = escape(course)
    safe_loc = escape(loc)

    persona_desc = f'<strong>{safe_name}</strong>'
    if persona:
        persona_desc += f' is a <strong>{safe_persona}</strong>'
    if mode and mode != 'Empty':
        persona_desc += f' interested in <strong>{safe_mode}</strong>'
    if course and course != 'Empty':
        persona_desc += f' for <strong>{safe_course}</strong>'
    if loc and loc != 'Empty':
        persona_desc += f' (<em>{safe_loc}</em>)'

    # Proposal A: Prior Call Memory
    last_call = lead.calls.order_by('-call_started_at').only('call_outcome', 'call_status', 'call_started_at', 'created_at', 'notes').first()
    if last_call:
        c_time = last_call.call_started_at or last_call.created_at
        ago_str = _format_rel_time(c_time)
        outcome_str = last_call.call_outcome or last_call.call_status or 'Completed'
        notes_snip = (last_call.notes or '').strip()
        if len(notes_snip) > 85:
            notes_snip = notes_snip[:82] + '...'
        note_display = f' - <em>"{escape(notes_snip)}"</em>' if notes_snip else ''
        call_memory_html = f'<strong>{escape(ago_str)}</strong> - Outcome: <span class="badge" style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:4px; font-weight:600;">{escape(outcome_str)}</span>{note_display}'
    else:
        call_memory_html = '<span style="color:#64748b; font-style:italic;">First contact - No prior calls recorded</span>'

    # Proposal B: Call Objective mapped to actual pipeline status
    lead_status = lead.status or 'New'
    objective_text = STATUS_CALL_OBJECTIVES.get(lead_status, STATUS_CALL_OBJECTIVES.get('New'))
    safe_status = escape(lead_status)
    safe_obj = escape(objective_text)

    # Proposal C: Objection Copilot strictly from admin-editable ApprovedOffer
    from .models_offers import ApprovedOffer
    active_offer = None
    if lead.product_id:
        active_offer = ApprovedOffer.objects.filter(is_active=True, product_id=lead.product_id).first()
    if not active_offer and lead.branch_id:
        active_offer = ApprovedOffer.objects.filter(is_active=True, branch_id=lead.branch_id).first()
    if not active_offer:
        active_offer = ApprovedOffer.objects.filter(is_active=True, product__isnull=True, branch__isnull=True).order_by('display_order', '-created_at').first()

    if active_offer:
        offer_html = f'<strong>{escape(active_offer.title)}:</strong> {escape(active_offer.approved_text)}'
    else:
        offer_html = '<span style="color:#64748b; font-style:italic;">Standard fee & syllabus schedule applies (no promotional offer active).</span>'

    html = f'''
<div style="display: flex; flex-direction: column; gap: 8px; width: 100%;">
  <div style="font-size: 0.9rem; color: #0f172a; line-height: 1.4;">
    {persona_desc}.
  </div>
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 8px; font-size: 0.825rem; background: #ffffff; padding: 10px 14px; border-radius: 8px; border: 1px solid #e2e8f0;">
    <div>
      <span style="font-weight: 700; color: #475569; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.04em; display: flex; align-items: center; gap: 4px; margin-bottom: 3px;">
        Prior Call Memory:
      </span>
      <div style="color: #1e293b;">{call_memory_html}</div>
    </div>
    <div>
      <span style="font-weight: 700; color: #475569; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.04em; display: flex; align-items: center; gap: 4px; margin-bottom: 3px;">
        Call Goal ({safe_status}):
      </span>
      <div style="color: #1e293b;">{safe_obj}</div>
    </div>
  </div>
  <div style="font-size: 0.825rem; background: #f8fafc; padding: 8px 12px; border-radius: 6px; border-left: 3px solid #2563eb; color: #334155;">
    <span style="font-weight: 700; color: #1d4ed8; font-size: 0.75rem; text-transform: uppercase; margin-right: 6px;">Approved Policy & Script:</span>
    {offer_html}
  </div>
</div>
'''
    return mark_safe(html.strip())
