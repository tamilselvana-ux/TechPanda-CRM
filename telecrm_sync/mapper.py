import logging
import threading
from contextlib import contextmanager
from datetime import datetime, timezone as dt_timezone
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
from leads.duplicates import normalize_phone
from leads.intake import resolve_branch as intake_resolve_branch, resolve_product as intake_resolve_product
from leads.models import Lead, LeadAssignmentHistory, LeadStatus, LeadStatusHistory
from products.models import Product
from .models import TeleCRMAction, TeleCRMLead, TeleCRMStatusMap, TeleCRMUser

logger = logging.getLogger(__name__)
User = get_user_model()

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
    "1": LeadStatus.NEW,
    "2": LeadStatus.INTERESTED,
    "3": LeadStatus.INTERESTED,
    "4": LeadStatus.INTERESTED,
    "5": LeadStatus.ENROLLED,
    "6": LeadStatus.LOST,
    "7": LeadStatus.NO_ANSWER,
    "8": LeadStatus.DEMO_SCHEDULED,
    "9": LeadStatus.VISITED,
    "10": LeadStatus.LATER,
    "11": LeadStatus.SWITCHED_OFF,
    "12": LeadStatus.CONTACTED,
    "13": LeadStatus.VISIT_SCHEDULED,
    "14": LeadStatus.LATER,
    "15": LeadStatus.NOT_INTERESTED,
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
    "fresh": LeadStatus.NEW,
    "new": LeadStatus.NEW,
    "contacted": LeadStatus.CONTACTED,
    "call taken": LeadStatus.CONTACTED,
    "just curious": LeadStatus.INTERESTED,
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
    "demo scheduled": LeadStatus.DEMO_SCHEDULED,
    "demo attended": LeadStatus.DEMO_SCHEDULED,
    "visit scheduled": LeadStatus.VISIT_SCHEDULED,
    "institute visit booked": LeadStatus.VISIT_SCHEDULED,
    "visited": LeadStatus.VISITED,
    "centre visited": LeadStatus.VISITED,
    "center visited": LeadStatus.VISITED,
    "walkin done": LeadStatus.VISITED,
    "counseling": LeadStatus.COUNSELING,
    "counselling": LeadStatus.COUNSELING,
    "online counselling initiated": LeadStatus.COUNSELING,
    "online counselling done": LeadStatus.COUNSELING,
    "enrolled": LeadStatus.ENROLLED,
    "converted": LeadStatus.ENROLLED,
    "joined": LeadStatus.ENROLLED,
    "admission done": LeadStatus.ENROLLED,
    "won": LeadStatus.ENROLLED,
    "not interested": LeadStatus.NOT_INTERESTED,
    "other language": LeadStatus.NOT_INTERESTED,
    "financial issue": LeadStatus.LATER,
    "not joined": LeadStatus.NOT_JOINED,
    "lost": LeadStatus.LOST,
    "junk": LeadStatus.LOST,
    "invalid": LeadStatus.LOST,
    "later": LeadStatus.LATER,
    "late": LeadStatus.LATER,
    "call later": LeadStatus.LATER,
    "historical": LeadStatus.HISTORICAL,
}

TERMINAL_LEAD_STATUSES = {
    LeadStatus.ENROLLED,
    LeadStatus.CONVERTED,
    LeadStatus.JOINED,
}

BRANCH_ALIASES = {
    "tnagar": "T. Nagar",
    "t. nagar": "T. Nagar",
    "t nagar": "T. Nagar",
    "tn": "T. Nagar",
    "_tn": "T. Nagar",
    "main branch": "T. Nagar",
    "corporate hq": "T. Nagar",
    "velachery": "Velachery",
    "velachary": "Velachery",
    "vel": "Velachery",
    "_vel": "Velachery",
    "sholinganallur": "Sholinganallur",
    "omr": "Sholinganallur",
    "sholinganallur (omr)": "Sholinganallur",
    "shol": "Sholinganallur",
    "_shol": "Sholinganallur",
    "anna nagar": "Anna Nagar",
    "annanagar": "Anna Nagar",
    "anna-nagar": "Anna Nagar",
    "an": "Anna Nagar",
    "_an": "Anna Nagar",
    "tambaram": "Tambaram",
    "kadaperi": "Tambaram",
    "tam": "Tambaram",
    "tham": "Tambaram",
    "_tam": "Tambaram",
    "_tham": "Tambaram",
    "porur": "Porur",
    "mount poonamallee": "Porur",
    "pr": "Porur",
    "_pr": "Porur",
    "coimbatore": "Coimbatore",
    "kovai": "Coimbatore",
    "gandhipuram": "Coimbatore",
    "cmb": "Coimbatore",
    "cbe": "Coimbatore",
    "_cmb": "Coimbatore",
}


def ms_to_datetime(ms_val: Any) -> Optional[datetime]:
    """Converts a Unix millisecond timestamp into a timezone-aware UTC datetime."""
    if not ms_val:
        return None
    try:
        ts = float(ms_val) / 1000.0
        return datetime.fromtimestamp(ts, tz=dt_timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def normalize_telecrm_phone(raw_phone: Any, telecrm_id: str = "") -> str:
    """
    Normalizes domestic phone numbers to 10-digit strings.
    International numbers with leading '+' preserve format.
    If absent or un-parseable, returns a stable surrogate identifier.
    """
    cleaned = str(raw_phone or "").strip()
    if not cleaned or cleaned.lower() in ("none", "null", "na", "0"):
        return f"NoPhone-{telecrm_id}" if telecrm_id else ""

    norm = normalize_phone(cleaned)
    if not norm or str(norm).startswith("NoPhone-"):
        return f"NoPhone-{telecrm_id}" if telecrm_id else ""

    if norm.startswith("+"):
        return norm
    return norm[-10:] if len(norm) >= 10 else norm


def resolve_telecrm_user(
    employee_uid_or_email: Any,
    user_cache: Optional[Dict[str, Optional[User]]] = None
) -> Optional[User]:
    """
    Resolves an action or lead employee reference to a native TechPanda CRM User.
    Handles internal TeleCRM UIDs (via TeleCRMUser mirror), direct email addresses,
    username prefixes, and contact phone numbers.
    """
    raw_id = str(employee_uid_or_email or "").strip()
    if not raw_id or raw_id in ("__telecrm", "telecrm", "__facebook", "null", "none"):
        return None

    if user_cache is not None and raw_id in user_cache:
        return user_cache[raw_id]

    matched_user: Optional[User] = None

    # 1. Lookup in TeleCRMUser mirror table by internal UID
    mapping = TeleCRMUser.objects.filter(uid=raw_id).select_related("crm_user").first()
    if mapping and mapping.crm_user:
        matched_user = mapping.crm_user
    elif mapping and mapping.email:
        matched_user = User.objects.filter(email__iexact=mapping.email).first()
        if matched_user:
            mapping.crm_user = matched_user
            mapping.save(update_fields=["crm_user"])

    # 2. Check if raw_id is an email address directly
    if not matched_user and "@" in raw_id:
        matched_user = User.objects.filter(email__iexact=raw_id).first()
        if not matched_user:
            prefix = raw_id.split("@")[0].strip()
            matched_user = User.objects.filter(username__iexact=prefix).first()

    # 3. Check by username
    if not matched_user:
        matched_user = User.objects.filter(username__iexact=raw_id).first()

    # 4. Check by 10-digit phone digits
    if not matched_user:
        clean_digits = "".join(ch for ch in raw_id if ch.isdigit())
        if len(clean_digits) >= 10:
            matched_user = User.objects.filter(phone__icontains=clean_digits[-10:]).first()

    if user_cache is not None:
        user_cache[raw_id] = matched_user

    return matched_user


def resolve_branch_from_text(
    branch_text: Any,
    fallback_name: str = "T. Nagar"
) -> Optional[Branch]:
    """
    Resolves a branch name using direct alias lookup, intake matching, or fallback to Main Branch.
    """
    raw = str(branch_text or "").strip()
    low = raw.lower()

    target_name = BRANCH_ALIASES.get(low)
    if target_name:
        b = Branch.objects.filter(name__iexact=target_name).first()
        if b:
            return b

    # Try existing intake resolver
    if raw:
        b = intake_resolve_branch(raw)
        if b:
            return b

    # Tag and substring checks
    clean = raw.upper().replace("-", "_").replace(" ", "_")
    if "_TN" in clean or "TNAGAR" in clean or "T_NAGAR" in clean:
        b = Branch.objects.filter(name="T. Nagar").first()
        if b:
            return b
    if "_VEL" in clean or "VELACHERY" in clean:
        b = Branch.objects.filter(name="Velachery").first()
        if b:
            return b
    if "_AN" in clean or "ANNANAGAR" in clean or "ANNA_NAGAR" in clean:
        b = Branch.objects.filter(name="Anna Nagar").first()
        if b:
            return b
    if "_CMB" in clean or "COIMBATORE" in clean or "_CBE" in clean:
        b = Branch.objects.filter(name="Coimbatore").first()
        if b:
            return b
    if "_PR" in clean or "PORUR" in clean:
        b = Branch.objects.filter(name="Porur").first()
        if b:
            return b
    if "_SHOL" in clean or "SHOLINGANALLUR" in clean or "OMR" in clean:
        b = Branch.objects.filter(name="Sholinganallur").first()
        if b:
            return b
    if "_TAM" in clean or "_THAM" in clean or "TAMBARAM" in clean:
        b = Branch.objects.filter(name="Tambaram").first()
        if b:
            return b

    # Default fallback
    return Branch.objects.filter(name__iexact=fallback_name).first() or Branch.objects.first()


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

    # 3. Substring heuristics
    s_low = s_name.lower()
    if s_low.startswith("won"):
        return LeadStatus.ENROLLED
    if "center visited" in s_low or "centre visited" in s_low:
        return LeadStatus.VISITED
    if "call not picked" in s_low:
        return LeadStatus.NO_ANSWER
    if "call not connected" in s_low:
        return LeadStatus.SWITCHED_OFF
    if "counsel" in s_low:
        return LeadStatus.COUNSELING
    if "visit" in s_low:
        return LeadStatus.VISIT_SCHEDULED

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
    clean_phone = normalize_telecrm_phone(raw_phone, telecrm_id)

    raw_name = str(fields.get("name") or "").strip()
    raw_email = str(fields.get("email_1") or fields.get("email") or "").strip().lower()
    raw_alt_phone = str(fields.get("alternate_phone") or "").strip()
    raw_status = raw_lead.get("status") or fields.get("status")
    raw_rating = raw_lead.get("rating")
    raw_employee = raw_lead.get("employeeid") or fields.get("assignee") or fields.get("assignee_name") or fields.get("employee")
    if not raw_employee and actions:
        for act in reversed(sorted(actions, key=lambda a: int(a.get("creationTimestamp") or 0))):
            if str(act.get("type", "")).upper() == "LEAD_ASSIGNMENT":
                assignedto = act.get("assignedto")
                if assignedto and not str(assignedto).startswith("__") and assignedto != "telecrm":
                    raw_employee = assignedto
                    break
    raw_branch = fields.get("base_branch")
    raw_course = fields.get("courses")
    created_ms = fields.get("created_on") or raw_lead.get("creationTimestamp")
    modified_ms = fields.get("modified_on")

    created_dt = ms_to_datetime(created_ms) or timezone.now()
    modified_dt = ms_to_datetime(modified_ms) or timezone.now()

    # Determine lead origin and possible inferred branch from earliest action
    derived_source, derived_platform, inferred_branch = determine_lead_source_and_platform(actions)
    branch_text_to_use = raw_branch or inferred_branch
    resolved_branch = resolve_branch_from_text(branch_text_to_use)
    resolved_product = resolve_product_from_text(raw_course)
    target_status = resolve_crm_status(raw_status)

    # Priority Rating: 0 = unrated -> None, 1..5 -> integer
    mapped_rating: Optional[int] = None
    if raw_rating is not None and str(raw_rating).isdigit():
        r_int = int(raw_rating)
        if 1 <= r_int <= 5:
            mapped_rating = r_int
        elif r_int == 0:
            mapped_rating = None

    # Resolve assigned user & owner role
    assigned_user = resolve_telecrm_user(raw_employee, user_cache)

    # 1. Deduplication lookup
    existing_lead: Optional[Lead] = None
    if clean_phone and not clean_phone.startswith("NoPhone-"):
        existing_lead = Lead.objects.filter(normalized_phone=clean_phone).first()

    was_created = False

    with transaction.atomic():
        if existing_lead:
            # ================= MERGE INTO EXISTING LEAD =================
            lead = existing_lead

            # 1. Terminal Status Protection: Do not overwrite terminal states
            if lead.status not in TERMINAL_LEAD_STATUSES and target_status:
                lead.status = target_status

            # 2. Name: Replace placeholder if valid name available
            if raw_name and raw_name.lower() not in ("na", "none", "null"):
                if not lead.name or lead.name.startswith("Lead ") or lead.name.lower() in ("na", "none"):
                    lead.name = raw_name

            # 3. Email: Fill if blank
            if raw_email and not lead.email:
                lead.email = raw_email

            # 4. Alternate Phone: Fill if blank
            if raw_alt_phone and not lead.alternate_phone:
                lead.alternate_phone = raw_alt_phone

            # 5. Branch: Fill if blank
            if resolved_branch and not lead.branch:
                lead.branch = resolved_branch

            # 6. Product: Fill if blank
            if resolved_product and not lead.product:
                lead.product = resolved_product

            # 7. Rating: Update if lead is unrated and TeleCRM has valid rating
            if mapped_rating is not None and lead.rating is None:
                lead.rating = mapped_rating

            # 8. User Assignment: Fill if lead currently has no assignee or update to matched telecaller
            if assigned_user:
                lead.assignment_status = "Assigned"
                if assigned_user.role == UserRole.TELECALLER:
                    lead.assigned_telecaller = assigned_user
                    lead.current_owner_type = "TELECALLER"
                elif assigned_user.role == UserRole.COUNSELOR:
                    lead.assigned_counselor = assigned_user
                    lead.current_owner_type = "COUNSELOR"
                elif assigned_user.role in (UserRole.BRANCH_HEAD, UserRole.SALES_HEAD):
                    lead.assigned_sales_head = assigned_user
                    lead.current_owner_type = "BRANCH_HEAD"
                else:
                    lead.assigned_telecaller = assigned_user
                    lead.current_owner_type = "TELECALLER"

            # 9. Custom Fields Aggregation
            if not isinstance(lead.custom_fields, dict):
                lead.custom_fields = {}
            lead.custom_fields["telecrm_id"] = telecrm_id
            if raw_course:
                lead.custom_fields["telecrm_course"] = raw_course
            if raw_rating is not None:
                lead.custom_fields["telecrm_rating"] = raw_rating
            for k in ("designation", "working_status", "interested_free_counselling", "calls_count", "connected_call_count", "total_call_duration"):
                if k in fields:
                    lead.custom_fields[f"telecrm_{k}"] = fields[k]

            lead.save()

        else:
            # ================= CREATE NEW LEAD =================
            was_created = True
            name_val = raw_name if (raw_name and raw_name.lower() not in ("na", "none", "null")) else f"Lead {clean_phone or telecrm_id}"

            custom_fields = {
                "telecrm_id": telecrm_id,
            }
            if raw_course:
                custom_fields["telecrm_course"] = raw_course
            if raw_rating is not None:
                custom_fields["telecrm_rating"] = raw_rating
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
                else:
                    assigned_telecaller = assigned_user
                    current_owner_type = "TELECALLER"

            lead = Lead.objects.create(
                name=name_val,
                phone=clean_phone or f"NoPhone-{telecrm_id}",
                normalized_phone=clean_phone if (clean_phone and not clean_phone.startswith("NoPhone-")) else None,
                email=raw_email,
                alternate_phone=raw_alt_phone,
                status=target_status,
                rating=mapped_rating,
                branch=resolved_branch,
                product=resolved_product,
                assigned_telecaller=assigned_telecaller,
                assigned_counselor=assigned_counselor,
                assigned_sales_head=assigned_sales_head,
                current_owner_type=current_owner_type,
                assignment_status=assignment_status,
                source=derived_source,
                platform=derived_platform,
                custom_fields=custom_fields,
            )

            # Preserve genuine historical creation timestamp
            Lead.objects.filter(id=lead.id).update(created_at=created_dt)
            lead.created_at = created_dt

        # Upsert TeleCRMLead mirror record
        tc_lead, _ = TeleCRMLead.objects.update_or_create(
            telecrm_id=telecrm_id,
            defaults={
                "phone": clean_phone,
                "raw": raw_lead,
                "crm_lead": lead,
                "telecrm_created_at": created_dt,
                "telecrm_modified_at": modified_dt,
            }
        )

    return lead, tc_lead, was_created


def ingest_lead_actions(
    lead: Lead,
    tc_lead: TeleCRMLead,
    raw_actions: List[Dict[str, Any]],
    user_cache: Optional[Dict[str, Optional[User]]] = None
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
                if a_type in ("OUTGOING_CALL", "INCOMING_CALL"):
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
                        if feedback == "CONNECTED" or duration_sec > 0:
                            c_status = CallStatus.CONNECTED
                        elif feedback in ("NO_ANSWER", "MISSED"):
                            c_status = CallStatus.NO_ANSWER
                        elif feedback == "BUSY":
                            c_status = CallStatus.BUSY

                        c_outcome = CallOutcome.FOLLOW_UP_REQUIRED
                        low_feedback = feedback.lower()
                        low_note = note_str.lower()
                        if "rnr" in low_note or "rnr" in low_feedback or "no answer" in low_feedback:
                            c_outcome = CallOutcome.RNR
                        elif "busy" in low_feedback or "busy" in low_note:
                            c_outcome = CallOutcome.BUSY
                        elif duration_sec >= 60 and c_status == CallStatus.CONNECTED:
                            c_outcome = CallOutcome.INTERESTED

                        rec_path = ""
                        rec_obj = action.get("callRecording")
                        if isinstance(rec_obj, dict):
                            rec_path = str(rec_obj.get("filePath") or "")

                        ch = CallHistory.objects.create(
                            lead=lead,
                            caller=actor_user or lead.assigned_telecaller,
                            telecaller=actor_user or lead.assigned_telecaller,
                            call_started_at=occurred_dt,
                            duration=duration_sec,
                            call_status=c_status,
                            call_outcome=c_outcome,
                            notes=note_str or feedback,
                            notes_completed=True,
                            recording_url=rec_path,
                        )
                        CallHistory.objects.filter(id=ch.id).update(created_at=occurred_dt)
                        crm_obj_type = "CallHistory"
                        crm_obj_id = str(ch.id)
                        mapped_ok = True

                elif a_type in ("USER_NOTE", "SYSTEM_NOTE"):
                    # ================= NOTE ACTIONS =================
                    text_val = str(action.get("text") or "").strip()
                    is_system = a_type == "SYSTEM_NOTE" or emp_uid in ("__telecrm", "telecrm", "__facebook")
                    action_title = "TeleCRM System Note" if is_system else "TeleCRM Note"
                    activity_user = None if is_system else (actor_user or lead.assigned_telecaller)

                    act = Activity.objects.create(
                        user=activity_user,
                        action=action_title,
                        object_type="Lead",
                        object_id=str(lead.id),
                        description=text_val,
                    )
                    Activity.objects.filter(id=act.id).update(timestamp=occurred_dt)
                    act.timestamp = occurred_dt
                    crm_obj_type = "Activity"
                    crm_obj_id = str(act.id)
                    mapped_ok = True

                elif a_type == "TASK_CREATION_ACTION":
                    # ================= TASK CREATION ACTIONS =================
                    task_name = str(action.get("taskName") or "Follow-up Task").strip()
                    task_type = str(action.get("taskType") or "").strip()
                    task_desc = f"Task: {task_name}"
                    if task_type:
                        task_desc += f" ({task_type})"
                    act = Activity.objects.create(
                        user=actor_user or lead.assigned_telecaller,
                        action="TeleCRM Task",
                        object_type="Lead",
                        object_id=str(lead.id),
                        description=task_desc,
                    )
                    Activity.objects.filter(id=act.id).update(timestamp=occurred_dt)
                    crm_obj_type = "Activity"
                    crm_obj_id = str(act.id)
                    mapped_ok = True

                elif a_type == "FIELD_CHANGE":
                    # ================= FIELD CHANGE ACTIONS =================
                    f_id = str(action.get("fieldid") or "field")
                    from_v = str(action.get("from") or "")
                    to_v = str(action.get("to") or "")
                    act = Activity.objects.create(
                        user=actor_user or lead.assigned_telecaller,
                        action="TeleCRM Field Update",
                        object_type="Lead",
                        object_id=str(lead.id),
                        description=f"Field updated ({f_id}): '{from_v}' -> '{to_v}'",
                    )
                    Activity.objects.filter(id=act.id).update(timestamp=occurred_dt)
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
                        changed_by=actor_user or lead.assigned_telecaller,
                        remarks="Status changed in TeleCRM",
                    )
                    LeadStatusHistory.objects.filter(id=lsh.id).update(created_at=occurred_dt)
                    lsh.created_at = occurred_dt
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
                        to_user=to_user or actor_user or lead.assigned_telecaller,
                        from_role="",
                        to_role=(to_user or actor_user or lead.assigned_telecaller).role if (to_user or actor_user or lead.assigned_telecaller) else "",
                        reason="Assignment synced from TeleCRM",
                    )
                    LeadAssignmentHistory.objects.filter(id=lah.id).update(created_at=occurred_dt)
                    lah.created_at = occurred_dt
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
                            crm_result="Imported from TeleCRM history",
                        )
                        FacebookLead.objects.filter(id=fb_lead.id).update(created_at=occurred_dt)
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
                        media_url = str(action.get("url") or "")

                        msg = Message.objects.create(
                            conversation=conv,
                            sender=sender_type,
                            message_type=msg_type,
                            message_text=msg_text,
                            media_file=media_url,
                            whatsapp_message_id=msg_id_tag,
                            status="read",
                        )
                        Message.objects.filter(id=msg.id).update(timestamp=occurred_dt)
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


def sync_and_provision_telecrm_team(members: List[Dict[str, Any]]) -> Dict[str, User]:
    """
    Provisions native CRM User records from TeleCRM team members metadata.
    Maps roles, extracts branch assignments from name/email, and links records.
    Returns mapping of email -> User.
    """
    import re
    email_to_user: Dict[str, User] = {}

    for m in members:
        email = str(m.get("email") or "").strip().lower()
        if not email:
            continue
        raw_name = str(m.get("name") or "").strip()
        phone = str(m.get("phone_number") or "").strip()
        perm = str(m.get("permission_template_name") or "").lower()

        role = UserRole.TELECALLER
        if "admin" in perm or "root" in perm:
            role = UserRole.ADMIN
        elif "counselor" in perm or "counsellor" in perm:
            role = UserRole.COUNSELOR
        elif "manager" in perm or "head" in perm:
            role = UserRole.BRANCH_HEAD

        clean_name = re.sub(r'_(TN|VEL|AN|CMB|PR|THAM|TAM|SHOL|OMR)$', '', raw_name, flags=re.I).strip()
        parts = clean_name.split(None, 1)
        first_name = parts[0] if parts else raw_name
        last_name = parts[1] if len(parts) > 1 else ""

        branch = resolve_branch_from_text(raw_name)

        user = User.objects.filter(email__iexact=email).first()
        if user:
            update_fields = []
            if not user.phone and phone:
                user.phone = phone
                update_fields.append("phone")
            if not user.branch and branch:
                user.branch = branch
                update_fields.append("branch")
            if update_fields:
                user.save(update_fields=update_fields)
        else:
            username_base = email.split("@")[0]
            uname = username_base
            idx = 1
            while User.objects.filter(username__iexact=uname).exists():
                uname = f"{username_base}_{idx}"
                idx += 1

            user = User.objects.create(
                username=uname,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role,
                branch=branch,
                is_active=True
            )
            user.set_unusable_password()
            user.save()

        email_to_user[email] = user

    return email_to_user


def build_and_save_uid_mappings() -> int:
    """
    Analyzes historical TeleCRMAction and TeleCRMLead records to deterministically
    link Firebase UIDs to native CRM Users.
    """
    from collections import defaultdict, Counter

    lead_emps: Dict[int, str] = {}
    for lid, raw in TeleCRMLead.objects.values_list("id", "raw"):
        emp = (raw.get("employeeid") or "").strip().lower()
        if emp and "@" in emp:
            lead_emps[lid] = emp

    uid_scores = defaultdict(Counter)
    for uid, lid in TeleCRMAction.objects.exclude(employee_uid="").values_list("employee_uid", "lead_id"):
        if not uid or uid.startswith("__") or uid == "telecrm":
            continue
        emp = lead_emps.get(lid)
        if emp:
            uid_scores[uid][emp] += 1

    mapped_count = 0
    for uid, counter in uid_scores.items():
        best_email, _ = counter.most_common(1)[0]
        user = User.objects.filter(email__iexact=best_email).first()
        TeleCRMUser.objects.update_or_create(
            uid=uid,
            defaults={
                "email": best_email,
                "name": user.get_full_name() or user.username if user else best_email,
                "crm_user": user
            }
        )
        mapped_count += 1

    return mapped_count


def remap_telecrm_history_and_assignees() -> Dict[str, int]:
    """
    One-time / administrative backfill repair that aligns all existing TeleCRM leads,
    call records, activity notes, and status transition logs to genuine historical
    timestamps, real assignees, and canonical LeadStatus stages using batch atomic blocks.
    """
    user_cache: Dict[str, Optional[User]] = {}
    results = {
        "leads_reassigned": 0,
        "calls_remapped": 0,
        "activities_remapped": 0,
        "status_history_remapped": 0,
        "assignment_history_remapped": 0,
    }

    # 1. Lead Assignee & Status Alignment (in atomic batch)
    with transaction.atomic():
        lead_qs = TeleCRMLead.objects.filter(crm_lead__isnull=False).select_related("crm_lead")
        for tl in lead_qs:
            c_lead = tl.crm_lead
            if not c_lead:
                continue

            raw_employee = tl.raw.get("employeeid")
            user = resolve_telecrm_user(raw_employee, user_cache)
            lead_dirty = False

            if user:
                if user.role == UserRole.TELECALLER and c_lead.assigned_telecaller != user:
                    c_lead.assigned_telecaller = user
                    c_lead.current_owner_type = "TELECALLER"
                    c_lead.assignment_status = "Assigned"
                    lead_dirty = True
                elif user.role == UserRole.COUNSELOR and c_lead.assigned_counselor != user:
                    c_lead.assigned_counselor = user
                    c_lead.current_owner_type = "COUNSELOR"
                    c_lead.assignment_status = "Assigned"
                    lead_dirty = True
                elif user.role in (UserRole.BRANCH_HEAD, UserRole.SALES_HEAD) and c_lead.assigned_sales_head != user:
                    c_lead.assigned_sales_head = user
                    c_lead.current_owner_type = "BRANCH_HEAD"
                    c_lead.assignment_status = "Assigned"
                    lead_dirty = True
                elif not c_lead.assigned_telecaller:
                    c_lead.assigned_telecaller = user
                    c_lead.current_owner_type = "TELECALLER"
                    c_lead.assignment_status = "Assigned"
                    lead_dirty = True

            raw_st = tl.raw.get("status")
            if raw_st and c_lead.status not in TERMINAL_LEAD_STATUSES:
                mapped_st = resolve_crm_status(raw_st)
                if mapped_st and c_lead.status != mapped_st:
                    c_lead.status = mapped_st
                    lead_dirty = True

            if lead_dirty:
                c_lead.save(update_fields=[
                    "assigned_telecaller",
                    "assigned_counselor",
                    "assigned_sales_head",
                    "current_owner_type",
                    "assignment_status",
                    "status"
                ])
                results["leads_reassigned"] += 1

    # 2. Activity Notes Alignment (Timestamp & User in atomic batch)
    with transaction.atomic():
        act_actions = list(TeleCRMAction.objects.filter(crm_object_type="Activity", mapped_ok=True).values("crm_object_id", "employee_uid", "occurred_at"))
        for a in act_actions:
            obj_id = a["crm_object_id"]
            if not obj_id:
                continue
            u = resolve_telecrm_user(a["employee_uid"], user_cache)
            Activity.objects.filter(id=obj_id).update(
                timestamp=a["occurred_at"],
                user=u
            )
            results["activities_remapped"] += 1

    # 3. Call History Alignment (Caller/Telecaller, Created_at in atomic batch)
    with transaction.atomic():
        call_actions = list(TeleCRMAction.objects.filter(crm_object_type="CallHistory", mapped_ok=True).values("crm_object_id", "employee_uid", "occurred_at", "lead__crm_lead__assigned_telecaller_id"))
        for a in call_actions:
            obj_id = a["crm_object_id"]
            if not obj_id:
                continue
            u = resolve_telecrm_user(a["employee_uid"], user_cache)
            caller_id = u.id if u else a.get("lead__crm_lead__assigned_telecaller_id")
            CallHistory.objects.filter(id=obj_id).update(
                caller_id=caller_id,
                telecaller_id=caller_id,
                created_at=a["occurred_at"]
            )
            results["calls_remapped"] += 1

    # 4. Status Transition History Alignment (Timestamp, Changed_By, Stages in atomic batch)
    with transaction.atomic():
        status_actions = list(TeleCRMAction.objects.filter(crm_object_type="LeadStatusHistory", mapped_ok=True).values("crm_object_id", "employee_uid", "occurred_at", "raw"))
        for a in status_actions:
            obj_id = a["crm_object_id"]
            if not obj_id:
                continue
            u = resolve_telecrm_user(a["employee_uid"], user_cache)
            raw_dict = a.get("raw") or {}
            from_id = raw_dict.get("fromStatusid")
            to_id = raw_dict.get("toStatusid")

            updates: Dict[str, Any] = {
                "created_at": a["occurred_at"],
                "changed_by": u,
            }
            if to_id:
                updates["new_status"] = resolve_crm_status("", to_id)
            if from_id:
                updates["old_status"] = resolve_crm_status("", from_id)

            LeadStatusHistory.objects.filter(id=obj_id).update(**updates)
            results["status_history_remapped"] += 1

    # 5. Assignment History Alignment (To User & Timestamp in atomic batch)
    with transaction.atomic():
        assign_actions = list(TeleCRMAction.objects.filter(crm_object_type="LeadAssignmentHistory", mapped_ok=True).values("crm_object_id", "occurred_at", "raw"))
        for a in assign_actions:
            obj_id = a["crm_object_id"]
            if not obj_id:
                continue
            raw_dict = a.get("raw") or {}
            assigned_to_uid = str(raw_dict.get("assignedto") or "").strip()
            to_user = resolve_telecrm_user(assigned_to_uid, user_cache)
            if to_user:
                LeadAssignmentHistory.objects.filter(id=obj_id).update(
                    to_user=to_user,
                    to_role=to_user.role,
                    created_at=a["occurred_at"]
                )
            else:
                LeadAssignmentHistory.objects.filter(id=obj_id).update(
                    created_at=a["occurred_at"]
                )
            results["assignment_history_remapped"] += 1

    return results
