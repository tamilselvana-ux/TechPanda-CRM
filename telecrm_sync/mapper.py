import logging
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Optional, Tuple
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from accounts.models import UserRole
from activities.models import Activity
from branches.models import Branch
from calls.models import CallHistory, CallOutcome, CallStatus
from chat.models import Conversation, Message
from fb_leads.models import FacebookLead
from followups.models import FollowUp, FollowUpStatus
from leads.duplicates import normalize_phone
from leads.intake import resolve_branch as intake_resolve_branch, resolve_product as intake_resolve_product
from leads.models import Lead, LeadAssignmentHistory, LeadStatus, LeadStatusHistory
from products.models import Product
from .models import SyncConflict, TeleCRMAction, TeleCRMLead, TeleCRMStatusMap, TeleCRMUser

logger = logging.getLogger(__name__)
User = get_user_model()

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
VENDOR_SUPPORT_EMAILS = {"murad.ali@telecrm.in", "mohd.ozair@telecrm.in"}

# Thread-local storage for side-effect suppression
_thread_locals = threading.local()


def is_sync_suppressed() -> bool:
    """Returns True if the current thread is executing under TeleCRM sync context."""
    return getattr(_thread_locals, "telecrm_sync_active", False)


@contextmanager
def suppress_sync_side_effects():
    """
    Context manager that suppresses side effects (notifications, auto-allocation,
    RNR alerts, duplicate warnings, and messaging webhooks) during sync or batch import.
    """
    prev_state = getattr(_thread_locals, "telecrm_sync_active", False)
    _thread_locals.telecrm_sync_active = True
    try:
        yield
    finally:
        _thread_locals.telecrm_sync_active = prev_state


# Default pipeline status fallback mapping from TeleCRM strings to TechPanda LeadStatus choices
DEFAULT_STATUS_MAP = {
    # Numerical Status IDs from TeleCRM Pipeline
    "1": LeadStatus.NEW,
    "2": LeadStatus.DISCUSSION,
    "3": LeadStatus.INTERESTED,
    "4": LeadStatus.INTERESTED,
    "5": LeadStatus.ENROLLED,
    "6": LeadStatus.LOST,
    "7": LeadStatus.NO_ANSWER,
    "8": LeadStatus.DEMO_ATTENDED,
    "9": LeadStatus.VISITED,
    "10": LeadStatus.LATER,
    "11": LeadStatus.SWITCHED_OFF,
    "12": LeadStatus.CONTACTED,
    "13": LeadStatus.VISIT_SCHEDULED,
    "14": LeadStatus.DISCUSSION,
    "15": LeadStatus.LOST,
    "16": LeadStatus.COUNSELING,
    "17": LeadStatus.COUNSELING,
    "18": LeadStatus.ENROLLED,
    "19": LeadStatus.ENROLLED,
    "20": LeadStatus.ENROLLED,
    "21": LeadStatus.ENROLLED,
    "22": LeadStatus.ENROLLED,
    "23": LeadStatus.VISITED,
    "24": LeadStatus.VISITED,
    "25": LeadStatus.VISITED,
    "26": LeadStatus.VISITED,
    "27": LeadStatus.VISITED,
    "28": LeadStatus.ENROLLED,
    "29": LeadStatus.VISITED,
    "30": LeadStatus.NO_ANSWER,
    "31": LeadStatus.NO_ANSWER,
    "32": LeadStatus.NO_ANSWER,
    "33": LeadStatus.NO_ANSWER,
    "34": LeadStatus.SWITCHED_OFF,
    "35": LeadStatus.SWITCHED_OFF,
    "36": LeadStatus.SWITCHED_OFF,
    "37": LeadStatus.SWITCHED_OFF,

    # String Status Labels (case-insensitive lowercase)
    "fresh": LeadStatus.NEW,
    "new": LeadStatus.NEW,
    "just curious": LeadStatus.DISCUSSION,
    "contacted": LeadStatus.CONTACTED,
    "call taken": LeadStatus.CONTACTED,
    "interested": LeadStatus.INTERESTED,
    "hot": LeadStatus.INTERESTED,
    "call not picked_1": LeadStatus.NO_ANSWER,
    "call not picked_2": LeadStatus.NO_ANSWER,
    "call not picked_3": LeadStatus.NO_ANSWER,
    "call not picked_4": LeadStatus.NO_ANSWER,
    "call not picked_5": LeadStatus.NO_ANSWER,
    "call not connected_1": LeadStatus.SWITCHED_OFF,
    "call not connected_2": LeadStatus.SWITCHED_OFF,
    "call not connected_3": LeadStatus.SWITCHED_OFF,
    "call not connected_4": LeadStatus.SWITCHED_OFF,
    "call not connected_5": LeadStatus.SWITCHED_OFF,
    "rnr": LeadStatus.NO_ANSWER,
    "ring no response": LeadStatus.NO_ANSWER,
    "busy": LeadStatus.BUSY,
    "switched off": LeadStatus.SWITCHED_OFF,
    "not reachable": LeadStatus.SWITCHED_OFF,
    "follow up": LeadStatus.FOLLOW_UP,
    "follow-up": LeadStatus.FOLLOW_UP,
    "discussion": LeadStatus.DISCUSSION,
    "in discussion": LeadStatus.DISCUSSION,
    "financial issue": LeadStatus.DISCUSSION,
    "demo scheduled": LeadStatus.DEMO_SCHEDULED,
    "demo attended": LeadStatus.DEMO_ATTENDED,
    "visit scheduled": LeadStatus.VISIT_SCHEDULED,
    "institute visit booked": LeadStatus.VISIT_SCHEDULED,
    "visited": LeadStatus.VISITED,
    "centre visited": LeadStatus.VISITED,
    "center visited": LeadStatus.VISITED,
    "center visited _ anna nagar": LeadStatus.VISITED,
    "center visited _ velachery": LeadStatus.VISITED,
    "center visited _ t nagar": LeadStatus.VISITED,
    "center visited _ tambaram": LeadStatus.VISITED,
    "center visited _ sholinganallur": LeadStatus.VISITED,
    "center visited _ coimbatore": LeadStatus.VISITED,
    "walkin done": LeadStatus.VISITED,
    "counseling": LeadStatus.COUNSELING,
    "counselling": LeadStatus.COUNSELING,
    "online counselling initiated": LeadStatus.COUNSELING,
    "online counselling done": LeadStatus.COUNSELING,
    "enrolled": LeadStatus.ENROLLED,
    "converted": LeadStatus.ENROLLED,
    "joined": LeadStatus.ENROLLED,
    "won_velachery": LeadStatus.ENROLLED,
    "won_sholinganallur": LeadStatus.ENROLLED,
    "won_porur": LeadStatus.ENROLLED,
    "won_anna nagar": LeadStatus.ENROLLED,
    "won_tambaram": LeadStatus.ENROLLED,
    "won_coimbatore": LeadStatus.ENROLLED,
    "won_tnagar": LeadStatus.ENROLLED,
    "admission done": LeadStatus.ENROLLED,
    "not interested": LeadStatus.NOT_INTERESTED,
    "not joined": LeadStatus.NOT_JOINED,
    "other language": LeadStatus.LOST,
    "lost": LeadStatus.LOST,
    "junk": LeadStatus.LOST,
    "invalid": LeadStatus.LOST,
    "late": LeadStatus.LATER,
    "later": LeadStatus.LATER,
    "call later": LeadStatus.LATER,
    "historical": LeadStatus.HISTORICAL,
}

TERMINAL_LEAD_STATUSES = {
    LeadStatus.ENROLLED,
    LeadStatus.CONVERTED,
    LeadStatus.JOINED,
}

FRESH_LEAD_STATUSES = {
    LeadStatus.NEW,
    "Fresh",
    "New",
}

LOST_LEAD_STATUSES = {
    LeadStatus.LOST,
    LeadStatus.NOT_INTERESTED,
    LeadStatus.NOT_JOINED,
}


def extract_telecrm_status_timestamp(
    raw_lead: Dict[str, Any],
    actions: Optional[List[Dict[str, Any]]] = None,
) -> Optional[datetime]:
    """
    Returns TeleCRM status-change timestamp using fields.status_last_updated_on,
    falling back to the latest STATUS_CHANGE action timestamp, then modified_on / creationTimestamp.
    """
    fields = raw_lead.get("fields") or {}
    st_ms = fields.get("status_last_updated_on")
    dt = ms_to_datetime(st_ms)
    if dt:
        return dt

    if actions:
        status_actions = [
            a for a in actions
            if str(a.get("type") or "").upper() == "STATUS_CHANGE" and a.get("creationTimestamp")
        ]
        if status_actions:
            latest = max(status_actions, key=lambda a: int(a.get("creationTimestamp") or 0))
            dt = ms_to_datetime(latest.get("creationTimestamp"))
            if dt:
                return dt

    return ms_to_datetime(fields.get("modified_on") or raw_lead.get("creationTimestamp"))


def evaluate_status_conflict(
    crm_status: str,
    crm_status_at: Optional[datetime],
    tc_status: str,
    tc_status_at: Optional[datetime],
    last_synced_status: str = "",
) -> Dict[str, Any]:
    """
    Applies deterministic status conflict rules between CRM and TeleCRM:
      1. Fresh/New never overwrites a non-Fresh status (either direction).
      2. Both non-Fresh: latest status-change timestamp wins (if CRM has no status history, TeleCRM wins).
      3. Won/Enrolled is protected: never auto-downgraded; differing status creates a SyncConflict.
      4. Lost vs Enrolled -> Enrolled.
      5. If BOTH sides changed status since last_synced_status -> apply rule 2 (or 3/4) + create SyncConflict.
    Returns dict: {applied_status, case, create_conflict, rule_applied}.
    """
    if not tc_status or crm_status == tc_status:
        return {
            "applied_status": crm_status or tc_status or LeadStatus.NEW,
            "case": "unchanged",
            "create_conflict": False,
            "rule_applied": "equal",
        }

    both_changed = bool(
        last_synced_status
        and crm_status != last_synced_status
        and tc_status != last_synced_status
        and crm_status != tc_status
    )

    # Rule 3: CRM Enrolled / Won is protected -> never auto-downgraded, always creates SyncConflict
    if crm_status in TERMINAL_LEAD_STATUSES:
        return {
            "applied_status": crm_status,
            "case": "protected_enrolled",
            "create_conflict": True,
            "rule_applied": "enrolled_protected_crm",
        }

    # Rule 1: Fresh/New never overwrites non-Fresh (including New -> Enrolled upgrade)
    if crm_status in FRESH_LEAD_STATUSES and tc_status not in FRESH_LEAD_STATUSES:
        return {
            "applied_status": tc_status,
            "case": "crm_fresh_to_telecrm",
            "create_conflict": False,
            "rule_applied": "crm_fresh_to_telecrm",
        }

    if tc_status in FRESH_LEAD_STATUSES and crm_status not in FRESH_LEAD_STATUSES:
        return {
            "applied_status": crm_status,
            "case": "telecrm_fresh_kept_crm",
            "create_conflict": False,
            "rule_applied": "telecrm_fresh_kept_crm",
        }

    # Rule 4 & 3: TeleCRM Enrolled / Won vs non-Fresh CRM -> Enrolled wins + creates SyncConflict
    if tc_status in TERMINAL_LEAD_STATUSES:
        return {
            "applied_status": tc_status,
            "case": "protected_enrolled",
            "create_conflict": True,
            "rule_applied": "lost_vs_enrolled" if crm_status in LOST_LEAD_STATUSES else "enrolled_protected_telecrm",
        }

    # Rule 2 & 5: Both non-Fresh -> latest status-change timestamp wins
    if crm_status_at is None:
        return {
            "applied_status": tc_status,
            "case": "newer_telecrm_won",
            "create_conflict": both_changed,
            "rule_applied": "no_crm_history_telecrm_wins",
        }

    if tc_status_at is not None and tc_status_at > crm_status_at:
        return {
            "applied_status": tc_status,
            "case": "newer_telecrm_won",
            "create_conflict": both_changed,
            "rule_applied": "newer_telecrm_timestamp",
        }

    return {
        "applied_status": crm_status,
        "case": "newer_crm_won",
        "create_conflict": both_changed,
        "rule_applied": "newer_crm_timestamp",
    }

BRANCH_ALIASES = {
    "tnagar": "T. Nagar",
    "t. nagar": "T. Nagar",
    "t nagar": "T. Nagar",
    "main branch": "T. Nagar",
    "corporate hq": "T. Nagar",
    "velachery": "Velachery",
    "velachary": "Velachery",
    "sholinganallur": "Sholinganallur",
    "omr": "Sholinganallur",
    "sholinganallur (omr)": "Sholinganallur",
    "anna nagar": "Anna Nagar",
    "annanagar": "Anna Nagar",
    "anna-nagar": "Anna Nagar",
    "tambaram": "Tambaram",
    "kadaperi": "Tambaram",
    "porur": "Porur",
    "mount poonamallee": "Porur",
    "coimbatore": "Coimbatore",
    "kovai": "Coimbatore",
    "gandhipuram": "Coimbatore",
}


def ms_to_datetime(ms_val: Any) -> Optional[datetime]:
    """Converts a Unix millisecond timestamp into a timezone-aware Asia/Kolkata datetime."""
    if not ms_val:
        return None
    try:
        ts = float(ms_val) / 1000.0
        return datetime.fromtimestamp(ts, tz=KOLKATA_TZ)
    except (ValueError, TypeError, OverflowError):
        return None


def get_or_create_telecrm_system_user() -> User:
    """
    Returns the designated non-staff 'TeleCRM System' user for vendor actions
    and automated system events (e.g. murad.ali@telecrm.in and mohd.ozair@telecrm.in).
    """
    u, created = User.objects.get_or_create(
        username="telecrm_system",
        defaults={
            "email": "system@telecrm.internal",
            "first_name": "TeleCRM",
            "last_name": "System",
            "is_active": False,
            "role": UserRole.TELECALLER,
        }
    )
    return u


def parse_telecrm_phone(raw_phone: Any, telecrm_id: str = "") -> Tuple[str, Optional[str], bool]:
    """
    Validates and normalizes TeleCRM phone numbers.
    Returns (display_phone, normalized_10_digit_or_none, phone_invalid).
    - Valid Indian mobile: after stripping optional +91 / 91 / 0091 / 0 prefix,
      exact 10 digits starting with 6-9.
    - Otherwise: preserves raw string (or NoPhone surrogate if empty), sets
      normalized_phone=None and phone_invalid=True.
    """
    raw_str = str(raw_phone or "").strip()
    surrogate = f"NoPhone-{telecrm_id}"[:20] if telecrm_id else "NoPhone"
    if not raw_str or raw_str.lower() in ("none", "null", "na", "0"):
        return surrogate, None, True

    digits = "".join(c for c in raw_str if c.isdigit())
    if len(digits) == 14 and digits.startswith("0091"):
        digits = digits[4:]
    elif len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]

    if len(digits) == 10 and digits[0] in ("6", "7", "8", "9"):
        return digits, digits, False

    return raw_str[:20], None, True


def normalize_telecrm_phone(raw_phone: Any, telecrm_id: str = "") -> str:
    """
    Normalizes domestic phone numbers to 10-digit strings when valid Indian mobile;
    otherwise returns raw value or NoPhone surrogate.
    """
    display_phone, norm_phone, _ = parse_telecrm_phone(raw_phone, telecrm_id)
    return norm_phone or display_phone


def resolve_telecrm_user(
    employee_uid_or_email: Any,
    user_cache: Optional[Dict[str, Optional[User]]] = None
) -> Optional[User]:
    """
    Resolves an action or lead employee reference to a native TechPanda CRM User.
    Handles internal TeleCRM UIDs (via TeleCRMUser mirror) and direct email addresses.
    Routes vendor support accounts (murad.ali, mohd.ozair) to 'TeleCRM System' user.
    """
    raw_id = str(employee_uid_or_email or "").strip()
    if not raw_id or raw_id in ("__telecrm", "telecrm", "__facebook", "null", "none"):
        return None

    if user_cache is not None and raw_id in user_cache:
        return user_cache[raw_id]

    # Vendor support check: Route to TeleCRM System user
    low_id = raw_id.lower()
    if low_id in VENDOR_SUPPORT_EMAILS or "telecrm.in" in low_id:
        system_user = get_or_create_telecrm_system_user()
        if user_cache is not None:
            user_cache[raw_id] = system_user
        return system_user

    matched_user: Optional[User] = None

    # 1. Lookup in TeleCRMUser mirror table by internal UID
    mapping = TeleCRMUser.objects.filter(uid=raw_id).select_related("crm_user").first()
    if mapping and mapping.crm_user:
        matched_user = mapping.crm_user
    elif mapping and mapping.email:
        m_email_low = mapping.email.strip().lower()
        if m_email_low in VENDOR_SUPPORT_EMAILS or "telecrm.in" in m_email_low:
            matched_user = get_or_create_telecrm_system_user()
        else:
            matched_user = User.objects.filter(email__iexact=mapping.email).first()
        if matched_user:
            mapping.crm_user = matched_user
            mapping.save(update_fields=["crm_user"])

    # 2. Check if raw_id is an email address directly
    if not matched_user and "@" in raw_id:
        matched_user = User.objects.filter(email__iexact=raw_id).first()

    # 3. Check by username
    if not matched_user:
        matched_user = User.objects.filter(username__iexact=raw_id).first()

    if user_cache is not None:
        user_cache[raw_id] = matched_user

    return matched_user


def resolve_branch_from_text(
    branch_text: Any,
    fallback_name: Optional[str] = None
) -> Optional[Branch]:
    """
    Resolves a branch name using direct alias lookup or intake matching.
    Returns None if empty or unmatched (never defaults to a physical branch).
    """
    raw = str(branch_text or "").strip()
    if not raw:
        return None
    low = raw.lower()

    target_name = BRANCH_ALIASES.get(low)
    if target_name:
        b = Branch.objects.filter(name__iexact=target_name).first()
        if b:
            return b

    # Try existing intake resolver
    b = intake_resolve_branch(raw)
    if b:
        return b

    if fallback_name:
        return Branch.objects.filter(name__iexact=fallback_name).first()
    return None


def resolve_product_from_text(course_text: Any) -> Optional[Product]:
    """
    Resolves a course or program name to a CRM Product instance.
    """
    raw = str(course_text or "").strip()
    if not raw:
        return None

    # Try existing intake resolver
    prod = intake_resolve_product(raw)
    if prod:
        return prod

    # Alias checks for common TeleCRM slugs
    low = raw.lower().replace("_", " ")
    if "data science" in low or "ai" in low:
        return Product.objects.filter(name__icontains="Data Science").first() or Product.objects.filter(name__icontains="AI").first()
    if "full stack" in low or "python" in low:
        return Product.objects.filter(name__icontains="Full Stack").first() or Product.objects.filter(name__icontains="Python").first()
    if "devops" in low or "cloud" in low:
        return Product.objects.filter(name__icontains="DevOps").first() or Product.objects.filter(name__icontains="Cloud").first()

    return None


def resolve_crm_status(raw_status: Any, status_id: Any = "") -> str:
    """
    Maps TeleCRM status name or ID into native TechPanda CRM LeadStatus choice.
    """
    s_name = str(raw_status or "").strip()
    s_id = str(status_id or "").strip()

    # 1. Check TeleCRMStatusMap database table
    if s_name:
        mapping = TeleCRMStatusMap.objects.filter(telecrm_status_name__iexact=s_name).first()
        if mapping and mapping.crm_status:
            return mapping.crm_status

    if s_id:
        mapping = TeleCRMStatusMap.objects.filter(telecrm_status_id=s_id).first()
        if mapping and mapping.crm_status:
            return mapping.crm_status

    # 2. Check DEFAULT_STATUS_MAP
    if s_name.lower() in DEFAULT_STATUS_MAP:
        return DEFAULT_STATUS_MAP[s_name.lower()]
    if s_id in DEFAULT_STATUS_MAP:
        return DEFAULT_STATUS_MAP[s_id]

    return LeadStatus.NEW


def determine_lead_source_and_platform(actions: Optional[List[Dict[str, Any]]]) -> Tuple[str, str, Optional[str]]:
    """
    Determines Lead.source, Lead.platform, and optionally an inferred branch name
    from the earliest chronological action associated with the lead.
    """
    if not actions:
        return "TeleCRM", "other", None

    sorted_actions = sorted(
        actions,
        key=lambda a: int(a.get("creationTimestamp") or 0)
    )
    first = sorted_actions[0]
    a_type = str(first.get("type", "")).upper()

    inferred_branch = None

    if a_type == "FACEBOOK":
        page_name = str(first.get("pageName") or "").strip()
        if page_name:
            low_page = page_name.lower()
            if "anna nagar" in low_page:
                inferred_branch = "Anna Nagar"
            elif "tambaram" in low_page:
                inferred_branch = "Tambaram"
            elif "velachery" in low_page:
                inferred_branch = "Velachery"
            elif "porur" in low_page:
                inferred_branch = "Porur"
            elif "coimbatore" in low_page or "kovai" in low_page:
                inferred_branch = "Coimbatore"
            elif "omr" in low_page or "sholinganallur" in low_page:
                inferred_branch = "Sholinganallur"
            elif "t nagar" in low_page or "t. nagar" in low_page:
                inferred_branch = "T. Nagar"
        return "Facebook", "facebook", inferred_branch

    if a_type in ("INCOMING_WHATSAPP_MSG", "OUTGOING_WHATSAPP_MSG"):
        ref = first.get("referralMsg") or {}
        if ref and isinstance(ref, dict):
            src_url = str(ref.get("sourceUrl", "")).lower()
            if "instagram" in src_url:
                return "Meta Ads", "instagram", None
            return "Meta Ads", "whatsapp", None
        return "WhatsApp", "whatsapp", None

    note_text = str(first.get("text") or "").lower()
    if "lead source: call logs" in note_text:
        return "Phone", "other", None
    if "lead source: whatsapp" in note_text:
        return "WhatsApp", "whatsapp", None

    emp = str(first.get("employeeid") or "")
    if "@" in emp:
        return "Manual", "direct", None

    return "TeleCRM", "other", None


def _sync_followup_for_lead(
    lead: Lead,
    followup_dt: Optional[datetime],
    assigned_telecaller: Optional[User],
    assigned_counselor: Optional[User],
    assigned_sales_head: Optional[User],
) -> Optional[str]:
    """
    Creates an open FollowUp task if next_follow-up_on is within the last 30 days or future.
    - Future / today (>= today IST): status = Pending
    - Past within 30 days (today - 30d <= date < today): status = Overdue
    - Older than 30 days: skipped
    Returns 'pending', 'overdue', 'skipped_old', or None.
    """
    if not followup_dt:
        return None
    today_ist = timezone.now().astimezone(KOLKATA_TZ).date()
    cutoff_date = today_ist - timedelta(days=30)
    f_date = followup_dt.astimezone(KOLKATA_TZ).date() if followup_dt.tzinfo else followup_dt.date()

    if f_date < cutoff_date:
        return "skipped_old"

    target_status = FollowUpStatus.OVERDUE if f_date < today_ist else FollowUpStatus.PENDING
    f_assignee = assigned_telecaller or assigned_counselor or assigned_sales_head
    FollowUp.objects.get_or_create(
        lead=lead,
        follow_up_date=f_date,
        defaults={
            "follow_up_time": followup_dt.astimezone(KOLKATA_TZ).time() if followup_dt.tzinfo else followup_dt.time(),
            "assigned_user": f_assignee,
            "telecaller": assigned_telecaller,
            "manager": assigned_sales_head,
            "status": target_status,
            "notes": "Follow-up synced from TeleCRM",
        }
    )
    return "overdue" if target_status == FollowUpStatus.OVERDUE else "pending"


def ingest_or_merge_lead(
    raw_lead: Dict[str, Any],
    actions: Optional[List[Dict[str, Any]]] = None,
    user_cache: Optional[Dict[str, Optional[User]]] = None
) -> Tuple[Lead, TeleCRMLead, bool]:
    """
    Deterministic ingestion of a single TeleCRM lead record.
    Deduplicates strictly by canonical 10-digit normalized phone.
    Merges without overwriting existing valid CRM data.
    Returns (crm_lead, telecrm_lead_mirror, was_created).
    """
    telecrm_id = str(raw_lead.get("id") or "").strip()
    if not telecrm_id:
        raise ValueError("TeleCRM lead payload missing required 'id' attribute")

    fields = raw_lead.get("fields") or {}
    raw_phone = fields.get("phone")
    display_phone, clean_norm_phone, is_phone_invalid = parse_telecrm_phone(raw_phone, telecrm_id)
    clean_phone = clean_norm_phone or display_phone

    raw_name = str(fields.get("name") or "").strip()
    raw_email = str(fields.get("email_1") or fields.get("email") or "").strip().lower()
    raw_alt_phone = str(fields.get("alternate_phone") or "").strip()
    raw_status = raw_lead.get("status") or fields.get("status")
    raw_rating = raw_lead.get("rating")
    raw_employee = raw_lead.get("employeeid")
    raw_branch = fields.get("base_branch")
    raw_course = fields.get("courses")
    created_ms = fields.get("created_on") or raw_lead.get("creationTimestamp")
    modified_ms = fields.get("modified_on")

    created_dt = ms_to_datetime(created_ms) or timezone.now()
    modified_dt = ms_to_datetime(modified_ms) or timezone.now()

    # Determine lead origin and possible inferred branch from earliest action
    derived_source, derived_platform, inferred_branch = determine_lead_source_and_platform(actions)
    resolved_product = resolve_product_from_text(raw_course)
    target_status = resolve_crm_status(raw_status)

    # Resolve assigned user & owner role first (needed for 4th branch fallback)
    assigned_user = resolve_telecrm_user(raw_employee, user_cache)

    # Branch precedence: status-derived branch > preferred_branch > base_branch > assignee branch > None ("Unknown")
    raw_status_label = str(fields.get("status") or raw_lead.get("status") or "").strip()
    raw_status_id = str(raw_lead.get("status") or fields.get("status_id") or "").strip()
    s_raw_lower = raw_status_label.lower()

    status_branch = None
    if s_raw_lower.startswith("won_"):
        branch_token = s_raw_lower[4:].strip()
        status_branch = resolve_branch_from_text(branch_token)
    elif "center visited _" in s_raw_lower or "centre visited _" in s_raw_lower:
        branch_token = s_raw_lower.split("_")[-1].strip()
        status_branch = resolve_branch_from_text(branch_token)

    raw_pref_branch = fields.get("preferred_branch")
    raw_base_branch = fields.get("base_branch")

    pref_branch_obj = resolve_branch_from_text(raw_pref_branch) if raw_pref_branch else None
    base_branch_obj = resolve_branch_from_text(raw_base_branch) if raw_base_branch else None
    assignee_branch_obj = getattr(assigned_user, "branch", None) if assigned_user else None

    if status_branch:
        resolved_branch = status_branch
        branch_source = "status"
    elif pref_branch_obj:
        resolved_branch = pref_branch_obj
        branch_source = "preferred"
    elif base_branch_obj:
        resolved_branch = base_branch_obj
        branch_source = "base"
    elif assignee_branch_obj:
        resolved_branch = assignee_branch_obj
        branch_source = "assignee"
    else:
        resolved_branch = None
        branch_source = "none"

    # Center visit scheduled date & contact preferences
    cv_scheduled_ms = fields.get("center_visit_scheduled_date")
    visit_scheduled_dt = ms_to_datetime(cv_scheduled_ms)
    do_not_call_val = bool(fields.get("do_not_call") in (True, "true", "True", 1, "1"))
    do_not_email_val = bool(fields.get("do_not_email") in (True, "true", "True", 1, "1"))

    # Next follow up datetime
    nfo_ms = fields.get("next_follow-up_on")
    followup_dt = ms_to_datetime(nfo_ms)

    # 2. Derive call attempt count from Call not picked_N / Call not connected_N and apply RNR rule
    import re
    attempt_match = re.search(r'call not (?:picked|connected)_(\d+)', s_raw_lower)
    call_attempts = int(attempt_match.group(1)) if attempt_match else 0
    is_recall = (call_attempts >= 3)

    # 3. Derive priority (Hot) and granular reason (Financial Issue, Other Language)
    derived_priority = "Hot" if s_raw_lower == "hot" else ""
    derived_reason = ""
    if s_raw_lower == "financial issue":
        derived_reason = "Financial Issue"
    elif s_raw_lower == "other language":
        derived_reason = "Other Language"

    # Priority Rating: 0 = unrated -> None, 1..5 -> integer
    mapped_rating: Optional[int] = None
    if raw_rating is not None and str(raw_rating).isdigit():
        r_int = int(raw_rating)
        if 1 <= r_int <= 5:
            mapped_rating = r_int
        elif r_int == 0:
            mapped_rating = None

    # Deduplication lookup (telecrm_id mirror first, then valid 10-digit normalized_phone)
    existing_lead: Optional[Lead] = None
    existing_mirror = TeleCRMLead.objects.filter(telecrm_id=telecrm_id).select_related("crm_lead").first()
    if existing_mirror and existing_mirror.crm_lead:
        existing_lead = existing_mirror.crm_lead
    elif clean_norm_phone:
        existing_lead = Lead.objects.filter(normalized_phone=clean_norm_phone).first()

    tc_status_at = extract_telecrm_status_timestamp(raw_lead, actions)
    was_created = False
    conflict_to_record = None

    with transaction.atomic():
        if existing_lead:
            # ================= MERGE INTO EXISTING LEAD =================
            lead = existing_lead
            prev_crm_status = lead.status
            latest_lsh = LeadStatusHistory.objects.filter(lead=lead).order_by("-created_at").first()
            crm_status_at = latest_lsh.created_at if latest_lsh else None
            last_synced_st = existing_mirror.last_synced_status if existing_mirror else ""

            conflict_res = evaluate_status_conflict(
                crm_status=prev_crm_status,
                crm_status_at=crm_status_at,
                tc_status=target_status,
                tc_status_at=tc_status_at,
                last_synced_status=last_synced_st,
            )
            applied_status = conflict_res["applied_status"]
            lead.status = applied_status

            if applied_status != prev_crm_status:
                lsh = LeadStatusHistory.objects.create(
                    lead=lead,
                    old_status=prev_crm_status,
                    new_status=applied_status,
                    changed_by=assigned_user,
                    remarks=f"[TeleCRM] Status updated ({conflict_res['rule_applied']})",
                )
                if tc_status_at:
                    LeadStatusHistory.objects.filter(pk=lsh.pk).update(created_at=tc_status_at)
            elif prev_crm_status != target_status:
                Activity.objects.create(
                    user=assigned_user,
                    action="TeleCRM Status Observation",
                    object_type="Lead",
                    object_id=str(lead.id),
                    description=(
                        f"[TeleCRM] Status in TeleCRM: {target_status} ({raw_status_label}) at "
                        f"{tc_status_at.strftime('%Y-%m-%d %H:%M') if tc_status_at else 'N/A'}; "
                        f"CRM kept {prev_crm_status} ({conflict_res['rule_applied']})"
                    ),
                    timestamp=tc_status_at or modified_dt,
                )

            if conflict_res["create_conflict"]:
                conflict_to_record = {
                    "crm_status": prev_crm_status,
                    "crm_status_at": crm_status_at,
                    "telecrm_status": target_status,
                    "telecrm_status_at": tc_status_at,
                    "telecrm_status_label": raw_status_label[:128],
                    "applied_status": applied_status,
                    "rule_applied": conflict_res["rule_applied"],
                }

            # 2. Name: Replace placeholder if valid name available
            if raw_name and raw_name.lower() not in ("na", "none", "null"):
                if not lead.name or lead.name.startswith("Lead ") or lead.name.lower() in ("na", "none"):
                    lead.name = raw_name[:255]

            # 3. Email: Fill if blank
            if raw_email and not lead.email:
                lead.email = raw_email[:255]

            # 4. Alternate Phone: Fill if blank
            if raw_alt_phone and not lead.alternate_phone:
                lead.alternate_phone = raw_alt_phone[:20]

            # 5. Branch: Fill if blank (do not overwrite existing CRM branch)
            if resolved_branch and not lead.branch:
                lead.branch = resolved_branch
                lead.branch_source = branch_source
            elif not lead.branch and not lead.branch_source:
                lead.branch_source = "none"

            # 6. Product: Fill if blank
            if resolved_product and not lead.product:
                lead.product = resolved_product

            # 7. Rating: Update if lead is unrated and TeleCRM has valid rating
            if mapped_rating is not None and lead.rating is None:
                lead.rating = mapped_rating

            # 8. User Assignment: Keep CRM assignee if set and active; else use TeleCRM assignee
            has_active_crm_assignee = any(
                u is not None and getattr(u, "is_active", False)
                for u in (lead.assigned_telecaller, lead.assigned_counselor, lead.assigned_sales_head, lead.assigned_branch_head)
            )
            if not has_active_crm_assignee and assigned_user:
                if assigned_user.role == UserRole.TELECALLER:
                    lead.assigned_telecaller = assigned_user
                    lead.current_owner_type = "TELECALLER"
                    lead.assignment_status = "Assigned"
                elif assigned_user.role == UserRole.COUNSELOR:
                    lead.assigned_counselor = assigned_user
                    lead.current_owner_type = "COUNSELOR"
                    lead.assignment_status = "Assigned"
                elif assigned_user.role in (UserRole.BRANCH_HEAD, UserRole.SALES_HEAD):
                    lead.assigned_sales_head = assigned_user
                    lead.current_owner_type = "BRANCH_HEAD"
                    lead.assignment_status = "Assigned"

            # 9. Custom Fields Aggregation
            if not isinstance(lead.custom_fields, dict):
                lead.custom_fields = {}
            lead.custom_fields["telecrm_id"] = telecrm_id
            if raw_course:
                lead.custom_fields["telecrm_course"] = raw_course
            if raw_rating is not None:
                lead.custom_fields["telecrm_rating"] = raw_rating
            if raw_pref_branch:
                lead.custom_fields["telecrm_preferred_branch"] = raw_pref_branch
            if raw_base_branch:
                lead.custom_fields["telecrm_base_branch"] = raw_base_branch
            for k in ("designation", "working_status", "interested_free_counselling", "calls_count", "connected_call_count", "total_call_duration"):
                if k in fields:
                    lead.custom_fields[f"telecrm_{k}"] = fields[k]

            # 10. TeleCRM Status Tracking, Priority, Reason & RNR Derivation
            lead.telecrm_status_id = raw_status_id[:64]
            lead.telecrm_status_label = raw_status_label[:128]
            if call_attempts > 0:
                lead.call_attempts_count = max(lead.call_attempts_count or 0, call_attempts)
            if is_recall:
                lead.is_recall_eligible = True
            if derived_priority:
                lead.priority = derived_priority
            if derived_reason:
                lead.sub_status_reason = derived_reason

            # 11. Concrete model fields: visit_scheduled_date, do_not_call, do_not_email
            if visit_scheduled_dt and not lead.visit_scheduled_date:
                lead.visit_scheduled_date = visit_scheduled_dt
            if do_not_call_val:
                lead.do_not_call = True
            if do_not_email_val:
                lead.do_not_email = True

            lead.save()

            # 12. Next Follow-up Task Creation (30-day rule)
            _sync_followup_for_lead(
                lead, followup_dt,
                lead.assigned_telecaller, lead.assigned_counselor, lead.assigned_sales_head
            )

        else:
            # ================= CREATE NEW LEAD =================
            was_created = True
            name_val = raw_name if (raw_name and raw_name.lower() not in ("na", "none", "null")) else f"Lead {display_phone or telecrm_id}"

            custom_fields = {
                "telecrm_id": telecrm_id,
            }
            if raw_course:
                custom_fields["telecrm_course"] = raw_course
            if raw_rating is not None:
                custom_fields["telecrm_rating"] = raw_rating
            if raw_pref_branch:
                custom_fields["telecrm_preferred_branch"] = raw_pref_branch
            if raw_base_branch:
                custom_fields["telecrm_base_branch"] = raw_base_branch
            for k in ("designation", "working_status", "interested_free_counselling", "calls_count", "connected_call_count", "total_call_duration"):
                if k in fields:
                    custom_fields[f"telecrm_{k}"] = fields[k]

            assigned_telecaller = None
            assigned_counselor = None
            assigned_sales_head = None
            current_owner_type = "UNASSIGNED"
            assignment_status = "Unassigned"

            if assigned_user:
                assignment_status = "Assigned"
                if assigned_user.role == UserRole.TELECALLER:
                    assigned_telecaller = assigned_user
                    current_owner_type = "TELECALLER"
                elif assigned_user.role == UserRole.COUNSELOR:
                    assigned_counselor = assigned_user
                    current_owner_type = "COUNSELOR"
                elif assigned_user.role in (UserRole.BRANCH_HEAD, UserRole.SALES_HEAD):
                    assigned_sales_head = assigned_user
                    current_owner_type = "BRANCH_HEAD"

            final_phone = (clean_norm_phone or display_phone or f"NoPhone-{telecrm_id}"[:20])[:20]

            lead = Lead.objects.create(
                name=(name_val or 'Lead')[:255],
                phone=final_phone,
                normalized_phone=clean_norm_phone,
                phone_invalid=is_phone_invalid,
                email=(raw_email or '')[:255],
                alternate_phone=(raw_alt_phone or '')[:20],
                status=target_status,
                rating=mapped_rating,
                branch=resolved_branch,
                branch_source=branch_source,
                product=resolved_product,
                assigned_telecaller=assigned_telecaller,
                assigned_counselor=assigned_counselor,
                assigned_sales_head=assigned_sales_head,
                current_owner_type=current_owner_type,
                assignment_status=assignment_status,
                source=derived_source,
                platform=derived_platform,
                custom_fields=custom_fields,
                telecrm_status_id=raw_status_id[:64],
                telecrm_status_label=raw_status_label[:128],
                priority=derived_priority,
                sub_status_reason=derived_reason,
                call_attempts_count=call_attempts,
                is_recall_eligible=is_recall,
                visit_scheduled_date=visit_scheduled_dt,
                do_not_call=do_not_call_val,
                do_not_email=do_not_email_val,
            )

            # Preserve genuine historical creation & modification timestamps in Asia/Kolkata
            Lead.objects.filter(id=lead.id).update(
                created_at=created_dt,
                updated_at=modified_dt
            )
            lead.created_at = created_dt
            lead.updated_at = modified_dt

            # Record initial status timeline entry with TeleCRM source & date
            init_lsh = LeadStatusHistory.objects.create(
                lead=lead,
                old_status="",
                new_status=lead.status,
                changed_by=assigned_user,
                remarks=f"[TeleCRM] Initial status ({raw_status_label or lead.status})",
            )
            LeadStatusHistory.objects.filter(pk=init_lsh.pk).update(created_at=tc_status_at or created_dt)

            # Next Follow-up Task Creation (30-day rule)
            _sync_followup_for_lead(
                lead, followup_dt,
                assigned_telecaller, assigned_counselor, assigned_sales_head
            )

        # Upsert TeleCRMLead mirror record
        tc_lead, _ = TeleCRMLead.objects.update_or_create(
            telecrm_id=telecrm_id,
            defaults={
                "phone": clean_phone,
                "raw": raw_lead,
                "crm_lead": lead,
                "telecrm_created_at": created_dt,
                "telecrm_modified_at": modified_dt,
                "last_synced_status": lead.status,
            }
        )

        if conflict_to_record:
            open_conflict = SyncConflict.objects.filter(
                lead=lead,
                status=SyncConflict.STATUS_OPEN,
            ).first()
            if open_conflict:
                for k, v in conflict_to_record.items():
                    setattr(open_conflict, k, v)
                open_conflict.telecrm_lead = tc_lead
                open_conflict.save()
            else:
                SyncConflict.objects.create(
                    lead=lead,
                    telecrm_lead=tc_lead,
                    **conflict_to_record,
                )

    return lead, tc_lead, was_created


def _download_and_link_recording(
    lead: Lead,
    tc_lead: TeleCRMLead,
    ch: CallHistory,
    rec_obj: Any,
    occurred_dt: datetime,
    duration_sec: int,
    a_type: str,
    actor_user: Optional[User],
    client: Optional[Any] = None,
    recording_stats: Optional[Dict[str, Any]] = None,
    download_recordings: bool = False,
) -> None:
    """
    Downloads a TeleCRM call recording into PrivateRecordingStorage (drive.CallRecording)
    and links CallHistory.recording_url to drive_stream_recording, keeping the original
    TeleCRM path/URL in CallRecording.drive_url (and CallHistory.recording_url if download fails).
    """
    import os
    import requests
    from django.core.files.base import ContentFile
    from django.urls import reverse
    from drive.models import CallRecording

    rec_path = ""
    rec_name = ""
    if isinstance(rec_obj, dict):
        rec_path = str(rec_obj.get("filePath") or rec_obj.get("url") or "").strip()
        rec_name = str(rec_obj.get("name") or "").strip()
    elif isinstance(rec_obj, str):
        rec_path = rec_obj.strip()

    if not rec_path:
        return

    if not rec_name:
        rec_name = os.path.basename(rec_path.split("?")[0]) or f"telecrm_call_{ch.id}.mp3"

    direction = "outgoing" if a_type == "OUTGOING_CALL" else "incoming"
    mins, secs = divmod(max(0, int(duration_sec or 0)), 60)
    dur_str = f"{mins:02d}:{secs:02d}"
    drive_key = f"telecrm_ch_{ch.id}"[:150]

    existing = CallRecording.objects.filter(drive_file_id=drive_key).first()
    if existing and existing.audio_file:
        stream_url = reverse("drive_stream_recording", args=[existing.pk])
        if ch.recording_url != stream_url:
            CallHistory.objects.filter(pk=ch.pk).update(recording_url=stream_url)
        return

    dl_url = ""
    err_reason = ""
    is_http = rec_path.lower().startswith("http://") or rec_path.lower().startswith("https://")
    if not download_recordings and not is_http:
        # Defer download: keep TeleCRM path in drive_url and CallHistory.recording_url for backfill
        CallRecording.objects.update_or_create(
            drive_file_id=drive_key,
            defaults={
                "source": CallRecording.SOURCE_APP,
                "lead": lead,
                "call_history": ch,
                "telecaller": actor_user,
                "file_name": rec_name[:255],
                "mobile_number": lead.phone[:30],
                "normalized_mobile_number": (lead.normalized_phone or "")[:20],
                "drive_url": rec_path[:500],
                "mime_type": "audio/mpeg",
                "duration": dur_str,
                "duration_seconds": duration_sec,
                "file_size": 0,
                "direction": direction,
                "archive_status": "PENDING",
                "match_status": "MATCHED",
                "recording_date": occurred_dt,
            }
        )
        if recording_stats is not None:
            recording_stats["pending"] = recording_stats.get("pending", 0) + 1
        return

    if is_http:
        dl_url = rec_path
    elif client is not None:
        try:
            resp = client.get_file_download_url(tc_lead.telecrm_id, rec_path)
            dl_url = str(resp.get("download_url") or resp.get("downloadUrl") or resp.get("url") or resp.get("signedUrl") or "").strip()
            if not dl_url:
                err_reason = f"No download_url in response: {str(resp)[:120]}"
        except Exception as exc:
            err_reason = str(exc)[:250]
    else:
        err_reason = "No TeleCRM client provided for download"

    audio_bytes = b""
    content_type = "audio/mpeg"
    if dl_url and not err_reason:
        try:
            r = requests.get(dl_url, timeout=30)
            if r.status_code == 200 and r.content:
                audio_bytes = r.content
                content_type = (r.headers.get("Content-Type") or "audio/mpeg").split(";")[0][:50]
            else:
                err_reason = f"HTTP {r.status_code} downloading audio"
        except Exception as exc:
            err_reason = f"Download error: {exc}"[:250]

    if audio_bytes:
        rec, _ = CallRecording.objects.update_or_create(
            drive_file_id=drive_key,
            defaults={
                "source": CallRecording.SOURCE_APP,
                "lead": lead,
                "call_history": ch,
                "telecaller": actor_user,
                "file_name": rec_name[:255],
                "mobile_number": lead.phone[:30],
                "normalized_mobile_number": (lead.normalized_phone or "")[:20],
                "drive_url": rec_path[:500],
                "mime_type": content_type,
                "duration": dur_str,
                "duration_seconds": duration_sec,
                "file_size": len(audio_bytes),
                "direction": direction,
                "archive_status": "ARCHIVED",
                "match_status": "MATCHED",
                "recording_date": occurred_dt,
            }
        )
        rec.audio_file.save(rec_name[:200], ContentFile(audio_bytes), save=True)
        stream_url = reverse("drive_stream_recording", args=[rec.pk])
        CallHistory.objects.filter(pk=ch.pk).update(recording_url=stream_url)
        ch.recording_url = stream_url
        if recording_stats is not None:
            recording_stats["downloaded"] = recording_stats.get("downloaded", 0) + 1
            recording_stats["bytes"] = recording_stats.get("bytes", 0) + len(audio_bytes)
    else:
        CallRecording.objects.update_or_create(
            drive_file_id=drive_key,
            defaults={
                "source": CallRecording.SOURCE_APP,
                "lead": lead,
                "call_history": ch,
                "telecaller": actor_user,
                "file_name": rec_name[:255],
                "mobile_number": lead.phone[:30],
                "normalized_mobile_number": (lead.normalized_phone or "")[:20],
                "drive_url": rec_path[:500],
                "mime_type": content_type,
                "duration": dur_str,
                "duration_seconds": duration_sec,
                "file_size": 0,
                "direction": direction,
                "archive_status": "FAILED",
                "match_status": "MATCHED",
                "unmatched_reason": err_reason[:255],
                "recording_date": occurred_dt,
            }
        )
        if recording_stats is not None:
            recording_stats["failed"] = recording_stats.get("failed", 0) + 1
            if err_reason and len(recording_stats.setdefault("errors", [])) < 10:
                recording_stats["errors"].append(err_reason)


def ingest_lead_actions(
    lead: Lead,
    tc_lead: TeleCRMLead,
    raw_actions: List[Dict[str, Any]],
    user_cache: Optional[Dict[str, Optional[User]]] = None,
    client: Optional[Any] = None,
    recording_stats: Optional[Dict[str, Any]] = None,
    download_recordings: bool = False,
) -> int:
    """
    Ingests and maps historical actions/timeline items into native CRM tables:
    - Calls -> calls.CallHistory (with Call Sync app deduplication)
    - Notes -> activities.Activity (SYSTEM_NOTE flagged as system)
    - Status changes -> leads.LeadStatusHistory
    - Assignments -> leads.LeadAssignmentHistory
    - Facebook leads -> fb_leads.FacebookLead (without intake hooks)
    - WhatsApp messages -> chat.Message & chat.Conversation
    Idempotent: skips any action ID already present in TeleCRMAction.
    Returns count of newly mapped actions.
    """
    if not raw_actions:
        return 0

    new_action_count = 0

    # Sort actions chronologically
    sorted_actions = sorted(
        raw_actions,
        key=lambda a: int(a.get("creationTimestamp") or 0)
    )

    for action in sorted_actions:
        action_id = str(action.get("id") or "").strip()
        if not action_id:
            continue

        # Idempotency check: Skip if already mapped
        if TeleCRMAction.objects.filter(telecrm_id=action_id).exists():
            continue

        a_type = str(action.get("type") or "UNKNOWN").upper()
        occurred_ms = action.get("creationTimestamp")
        occurred_dt = ms_to_datetime(occurred_ms) or timezone.now()
        emp_uid = str(action.get("employeeid") or "")
        actor_user = resolve_telecrm_user(emp_uid, user_cache)

        crm_obj_type = ""
        crm_obj_id = ""
        mapped_ok = False
        error_msg = ""

        try:
            with transaction.atomic():
                if a_type in ("OUTGOING_CALL", "INCOMING_CALL", "MISSED_CALL"):
                    # ================= CALL DEDUPLICATION =================
                    duration_sec = int(action.get("duration") or 0)
                    feedback = str(action.get("feedback") or "").upper()
                    note_str = str(action.get("note") or "")

                    # Check for Call Sync app deduplication: same lead, within +/- 60s, matching duration (+/- 5s)
                    start_min = occurred_dt.timestamp() - 60
                    start_max = occurred_dt.timestamp() + 60
                    dt_min = datetime.fromtimestamp(start_min, tz=dt_timezone.utc)
                    dt_max = datetime.fromtimestamp(start_max, tz=dt_timezone.utc)

                    matching_call = CallHistory.objects.filter(
                        lead=lead,
                        call_started_at__range=(dt_min, dt_max),
                        duration__range=(max(0, duration_sec - 5), duration_sec + 5)
                    ).first()

                    if matching_call:
                        # Retain existing Call Sync app record (it possesses recording)
                        crm_obj_type = "CallHistory"
                        crm_obj_id = str(matching_call.id)
                        mapped_ok = True
                    else:
                        # Determine call status and outcome
                        c_status = CallStatus.COMPLETED
                        if a_type == "MISSED_CALL" or feedback in ("NO_ANSWER", "MISSED", "NA"):
                            c_status = CallStatus.NO_ANSWER
                        elif feedback == "CONNECTED" or duration_sec > 0:
                            c_status = CallStatus.CONNECTED
                        elif feedback == "BUSY":
                            c_status = CallStatus.BUSY

                        c_outcome = CallOutcome.FOLLOW_UP_REQUIRED
                        low_feedback = feedback.lower()
                        low_note = note_str.lower()
                        if a_type == "MISSED_CALL" or "rnr" in low_note or "rnr" in low_feedback or "no answer" in low_feedback or low_feedback == "na":
                            c_outcome = CallOutcome.RNR
                        elif "busy" in low_feedback or "busy" in low_note:
                            c_outcome = CallOutcome.BUSY
                        elif duration_sec >= 60 and c_status == CallStatus.CONNECTED:
                            c_outcome = CallOutcome.INTERESTED

                        rec_path = ""
                        rec_obj = action.get("callRecording")
                        if isinstance(rec_obj, dict):
                            rec_path = str(rec_obj.get("filePath") or rec_obj.get("url") or "")
                        elif isinstance(rec_obj, str):
                            rec_path = rec_obj

                        ch = CallHistory.objects.create(
                            lead=lead,
                            caller=actor_user,
                            telecaller=actor_user,
                            call_started_at=occurred_dt,
                            duration=duration_sec,
                            call_status=c_status,
                            call_outcome=c_outcome,
                            notes=note_str or feedback,
                            recording_url="",
                            telecrm_recording_path=rec_path[:500],
                        )
                        crm_obj_type = "CallHistory"
                        crm_obj_id = str(ch.id)
                        mapped_ok = True

                elif a_type == "PAYMENT":
                    # ================= PAYMENT ACTIONS =================
                    amount = action.get("amount") or 0
                    currency = action.get("currency") or "INR"
                    status_p = action.get("status") or "COMPLETED"
                    mode_p = action.get("paymentMode") or "UNKNOWN"
                    tx_id = action.get("transactionId") or action_id

                    act = Activity.objects.create(
                        user=actor_user,
                        action="TeleCRM Payment",
                        object_type="Lead",
                        object_id=str(lead.id),
                        description=f"Payment of {currency} {amount} via {mode_p} (Status: {status_p}, TxID: {tx_id})",
                        timestamp=occurred_dt
                    )
                    crm_obj_type = "Activity"
                    crm_obj_id = str(act.id)
                    mapped_ok = True

                elif a_type in ("USER_NOTE", "SYSTEM_NOTE"):
                    # ================= NOTE ACTIONS =================
                    text_val = str(action.get("text") or "").strip()
                    is_system = a_type == "SYSTEM_NOTE" or emp_uid in ("__telecrm", "telecrm", "__facebook")
                    action_title = "TeleCRM System Note" if is_system else "TeleCRM Note"
                    activity_user = None if is_system else actor_user

                    act = Activity.objects.create(
                        user=activity_user,
                        action=action_title,
                        object_type="Lead",
                        object_id=str(lead.id),
                        description=text_val,
                        timestamp=occurred_dt
                    )
                    crm_obj_type = "Activity"
                    crm_obj_id = str(act.id)
                    mapped_ok = True

                elif a_type == "STATUS_CHANGE":
                    # ================= STATUS CHANGE ACTIONS =================
                    from_id = action.get("fromStatusid")
                    to_id = action.get("toStatusid")
                    old_st = resolve_crm_status("", from_id) if from_id else ""
                    new_st = resolve_crm_status("", to_id) if to_id else LeadStatus.NEW

                    lsh = LeadStatusHistory.objects.create(
                        lead=lead,
                        old_status=old_st,
                        new_status=new_st,
                        changed_by=actor_user,
                        remarks="[TeleCRM] Status changed in TeleCRM",
                    )
                    LeadStatusHistory.objects.filter(pk=lsh.pk).update(created_at=occurred_dt)
                    crm_obj_type = "LeadStatusHistory"
                    crm_obj_id = str(lsh.id)
                    mapped_ok = True

                elif a_type == "LEAD_ASSIGNMENT":
                    # ================= LEAD ASSIGNMENT ACTIONS =================
                    assigned_to_uid = str(action.get("assignedto") or "").strip()
                    to_user = resolve_telecrm_user(assigned_to_uid, user_cache)

                    lah = LeadAssignmentHistory.objects.create(
                        lead=lead,
                        from_user=None,
                        to_user=to_user,
                        from_role="",
                        to_role=to_user.role if to_user else "",
                        reason="Assignment synced from TeleCRM",
                        created_at=occurred_dt
                    )
                    crm_obj_type = "LeadAssignmentHistory"
                    crm_obj_id = str(lah.id)
                    mapped_ok = True

                elif a_type == "FACEBOOK":
                    # ================= FACEBOOK LEAD ACTIONS =================
                    lead_fb_id = str(action.get("leadFbId") or f"telecrm_fb_{action_id}").strip()
                    existing_fb = FacebookLead.objects.filter(leadgen_id=lead_fb_id).first()
                    if existing_fb:
                        crm_obj_type = "FacebookLead"
                        crm_obj_id = str(existing_fb.id)
                        mapped_ok = True
                    else:
                        ad_det = action.get("adDetails") or {}
                        fb_lead = FacebookLead.objects.create(
                            leadgen_id=lead_fb_id,
                            lead=lead,
                            full_name=lead.name,
                            phone=lead.phone,
                            email=lead.email,
                            form_name=str(action.get("formName") or ""),
                            form_id=str(action.get("formid") or ""),
                            page_id=str(action.get("pageid") or ""),
                            ad_name=str(ad_det.get("adName") or ""),
                            campaign_name=str(ad_det.get("camapignName") or ad_det.get("campaignName") or ""),
                            ad_id=str(ad_det.get("adId") or ""),
                            platform="facebook",
                            all_answers=action,
                            crm_result="telecrm_sync",
                        )
                        crm_obj_type = "FacebookLead"
                        crm_obj_id = str(fb_lead.id)
                        mapped_ok = True

                elif a_type in ("INCOMING_WHATSAPP_MSG", "OUTGOING_WHATSAPP_MSG"):
                    # ================= WHATSAPP MESSAGE ACTIONS =================
                    msg_text = str(action.get("messageText") or "").strip()
                    msg_id_tag = f"telecrm_{action_id}"

                    existing_msg = Message.objects.filter(whatsapp_message_id=msg_id_tag).first()
                    if existing_msg:
                        crm_obj_type = "Message"
                        crm_obj_id = str(existing_msg.id)
                        mapped_ok = True
                    else:
                        phone_to_use = lead.normalized_phone or lead.phone
                        conv, _ = Conversation.objects.get_or_create(
                            phone_number=phone_to_use,
                            defaults={
                                "customer_name": lead.name or f"Lead {phone_to_use}",
                                "last_message": msg_text[:255],
                                "last_message_time": occurred_dt,
                            }
                        )

                        sender_type = "customer" if a_type == "INCOMING_WHATSAPP_MSG" else "agent"
                        msg_type = "document" if action.get("url") else "text"
                        media_url = str(action.get("url") or "").strip()
                        if media_url:
                            if not msg_text:
                                msg_text = media_url
                            elif media_url not in msg_text:
                                msg_text = f"{msg_text} ({media_url})"

                        msg = Message.objects.create(
                            conversation=conv,
                            sender=sender_type,
                            message_type=msg_type,
                            message_text=msg_text,
                            media_file=None,
                            whatsapp_message_id=msg_id_tag,
                            status="read",
                            timestamp=occurred_dt
                        )
                        conv.last_message = msg_text[:255]
                        conv.last_message_time = occurred_dt
                        conv.save(update_fields=["last_message", "last_message_time"])

                        crm_obj_type = "Message"
                        crm_obj_id = str(msg.id)
                        mapped_ok = True

                else:
                    # Generic action mirror
                    mapped_ok = True

        except Exception as ex:
            logger.exception("Error mapping TeleCRM action %s (type %s): %s", action_id, a_type, ex)
            error_msg = str(ex)
            mapped_ok = False

        TeleCRMAction.objects.create(
            telecrm_id=action_id,
            lead=tc_lead,
            type=a_type,
            occurred_at=occurred_dt,
            employee_uid=emp_uid,
            raw=action,
            crm_object_type=crm_obj_type,
            crm_object_id=crm_obj_id,
            mapped_ok=mapped_ok,
            error=error_msg
        )
        if mapped_ok:
            new_action_count += 1

    return new_action_count


def sync_telecrm_lead_payload(
    raw_lead: Dict[str, Any],
    raw_actions: Optional[List[Dict[str, Any]]] = None,
    user_cache: Optional[Dict[str, Optional[User]]] = None
) -> Dict[str, Any]:
    """
    Main entry point for syncing a lead and its actions under side-effect suppression.
    """
    with suppress_sync_side_effects():
        lead, tc_lead, was_created = ingest_or_merge_lead(raw_lead, raw_actions, user_cache)
        actions_mapped = 0
        if raw_actions:
            actions_mapped = ingest_lead_actions(lead, tc_lead, raw_actions, user_cache)

        return {
            "lead_id": lead.id,
            "telecrm_id": tc_lead.telecrm_id,
            "was_created": was_created,
            "actions_mapped": actions_mapped,
        }
