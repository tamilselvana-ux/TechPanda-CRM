"""
Superadmin CRM Assistant - Pure Local Rule-Based NLP & Query Engine
Zero-AI, Zero-API, Zero External Tools. 100% Deterministic & Private.
"""
import re
from datetime import datetime, time, timedelta
from difflib import get_close_matches
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.urls import reverse

from accounts.models import User, UserRole
from branches.models import Branch
from leads.models import (
    Lead, LeadStatus, TelecallerLeadSetup, DuplicateLeadRecord,
    CANONICAL_LEAD_SOURCES
)
try:
    from leads.models import Enrollment, PaymentTransaction
except ImportError:
    Enrollment = None
    PaymentTransaction = None

try:
    from followups.models import FollowUp
except ImportError:
    FollowUp = None

try:
    from calls.models import CallLog, CallDevice, CallHistory
except ImportError:
    CallLog = None
    CallDevice = None
    CallHistory = None

try:
    from activities.models import Activity
except ImportError:
    Activity = None


# Knowledge Base of CRM Workflows, Settings & How-To SOPs
CRM_KNOWLEDGE_BASE = [
    {
        'keywords': ['add branch', 'create branch', 'new branch', 'make branch'],
        'title': 'How to Add a New Branch',
        'content': 'To create a new branch:\n1. Navigate to Settings &gt; Branches or the Branch Management directory.\n2. Click "Add Branch".\n3. Fill in Branch Name, Branch Code, Address, and Contact details.\n4. Click Save to provision the branch.',
        'action': {'label': 'Open Branches Management', 'url': '/admin/branches/'}
    },
    {
        'keywords': ['add counselor', 'create counselor', 'new counselor', 'register counselor'],
        'title': 'How to Add a Counselor',
        'content': 'To add a new counselor:\n1. Navigate to Users &gt; Create User.\n2. Select role "Counselor".\n3. Assign them to their primary Branch.\n4. Enter First Name, Last Name, Email, and Phone.\n5. Click "Save &amp; Send Invitation". The counselor will receive an account setup email.',
        'action': {'label': 'Create User Directory', 'url': '/admin/users/'}
    },
    {
        'keywords': ['add telecaller', 'create telecaller', 'new telecaller', 'telecaller invite'],
        'title': 'How to Add a Telecaller',
        'content': 'To create a telecaller with the simplified flow:\n1. Go to Telecallers &gt; "Add Telecaller".\n2. Enter First Name, Last Name, Email, and Phone (Counselor and Branch are optional).\n3. Click "Create &amp; Send Invite".\n4. Unassigned telecallers can later be assigned or reassigned via the bulk action bar on the Telecallers list.',
        'action': {'label': 'Add Telecaller', 'url': '/admin/telecallers/create/'}
    },
    {
        'keywords': ['bulk assign', 'reassign telecaller', 'change branch telecaller', 'remove counselor'],
        'title': 'Bulk Assigning & Reassigning Telecallers',
        'content': 'To reassign telecallers in bulk:\n1. Go to Admin &gt; Telecallers list.\n2. Select one or more telecallers using the checkboxes on the left.\n3. The sticky action bar will appear at the bottom.\n4. Click "Assign to Counselor", "Change Branch", "Remove Counselor", or "Remove Branch".\n5. Confirm the action in the prompt to apply changes atomically.',
        'action': {'label': 'Go to Telecallers List', 'url': '/admin/telecallers/'}
    },
    {
        'keywords': ['centralized lead allocation', 'centralized setup', 'pool leads', 'centralized hub', 'multi branch leads'],
        'title': 'Centralized Lead Allocation Hub',
        'content': 'The Centralized Lead Allocation Hub allows pooling leads across all branches:\n1. Navigate to Settings &gt; Lead Setup.\n2. Click the top "Centralized Lead Allocation Hub" card.\n3. Select any digital source (e.g., WhatsApp, Meta Ads, Website).\n4. Check the telecallers across any branch who should receive leads from this pool.\n5. Enter percentage allocations so the total equals exactly 100% and click Save.',
        'action': {'label': 'Go to Lead Setup', 'url': '/admin/settings/lead-setup/'}
    },
    {
        'keywords': ['lead allocation', 'allocation percentage', 'source setup', '100% allocation'],
        'title': 'Configuring Lead Allocation',
        'content': 'Lead allocation rules enforce strict 100% distribution:\n1. Go to Settings &gt; Lead Setup.\n2. Choose a specific Branch or the Centralized Hub.\n3. Select the Lead Source tab.\n4. Check the active telecallers and set allocation %.\n5. The allocation total must equal exactly 100% to activate automated distribution.',
        'action': {'label': 'Configure Lead Setup', 'url': '/admin/settings/lead-setup/'}
    },
    {
        'keywords': ['export report', 'reports', 'download leads', 'export excel', 'financial report'],
        'title': 'Exporting Reports & Analytics',
        'content': 'To generate and export CRM reports:\n1. Go to Reports in the main navigation menu.\n2. Choose from Lead Reports, Counselor RNR, Telecaller Performance, or Financial Summary.\n3. Select your date filter (Today, This Week, Custom Month).\n4. Click "Export to Excel" or "Download PDF".',
        'action': {'label': 'Open Reports Hub', 'url': '/admin/reports/'}
    },
    {
        'keywords': ['duplicate leads', 'merge duplicates', 'duplicate detection', 'clean duplicates'],
        'title': 'Managing Duplicate Leads',
        'content': 'The CRM automatically detects matching leads by phone number or email:\n1. Go to Leads &gt; Duplicate Leads.\n2. Review grouped records showing match criteria and conflicting assignees.\n3. Use "Merge" to consolidate notes and activities into the master record.',
        'action': {'label': 'View Duplicate Leads', 'url': '/admin/duplicate-leads/'}
    },
    {
        'keywords': ['call sync', 'android app', 'call recording', 'device sync'],
        'title': 'Call Sync & Android App Setup',
        'content': 'Telecaller call logs sync automatically via the TechPanda Call Sync app:\n1. Telecallers log into the mobile APK on company Android devices.\n2. Call durations, timestamps, and recordings sync to the server in real-time.\n3. View live call activity under Calls &gt; Call Logs.',
        'action': {'label': 'View Call Logs', 'url': '/admin/calls/'}
    },
    {
        'keywords': ['whatsapp', 'meta ads', 'facebook leads', 'channels'],
        'title': 'Inbound Lead Channels & Integrations',
        'content': 'TechPanda CRM connects directly with WhatsApp Cloud API and Meta Lead Ads:\n1. WhatsApp chat conversations sync into the unified Chat Inbox.\n2. Meta Lead Ad webhooks automatically ingest leads with zero delay.\n3. All incoming leads follow your configured Lead Setup percentages.',
        'action': {'label': 'Open Chat Inbox', 'url': '/chat/'}
    }
]


def _get_date_range(query_lower):
    """Parses date tokens into start_datetime, end_datetime, and label."""
    now = timezone.now()
    today_start = timezone.make_aware(datetime.combine(now.date(), time.min))
    today_end = timezone.make_aware(datetime.combine(now.date(), time.max))

    if 'today' in query_lower:
        return today_start, today_end, "Today"
    elif 'yesterday' in query_lower:
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_end - timedelta(days=1)
        return yesterday_start, yesterday_end, "Yesterday"
    elif 'this week' in query_lower or 'week' in query_lower:
        week_start = today_start - timedelta(days=today_start.weekday())
        return week_start, today_end, "This Week"
    elif 'last week' in query_lower:
        week_start = today_start - timedelta(days=today_start.weekday() + 7)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        return week_start, week_end, "Last Week"
    elif 'this month' in query_lower or 'month' in query_lower:
        month_start = today_start.replace(day=1)
        return month_start, today_end, "This Month"
    elif 'last month' in query_lower:
        first_this_month = today_start.replace(day=1)
        last_month_end = first_this_month - timedelta(seconds=1)
        last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0)
        return last_month_start, last_month_end, "Last Month"
    
    return None, None, "All Time"


def _extract_branch(query_lower):
    """Finds matching active branch from text."""
    branches = list(Branch.objects.filter(status='Active'))
    for b in branches:
        b_name_clean = b.name.lower().replace('.', '').replace('-', ' ')
        b_code = getattr(b, 'code', '').lower()
        if b_name_clean in query_lower or (b_code and b_code in query_lower):
            return b

    # Partial token matching (excluding generic words like branch, center, test)
    ignored_tokens = {'branch', 'center', 'centre', 'test', 'audit', 'leads', 'setup'}
    for b in branches:
        tokens = b.name.lower().split()
        for tok in tokens:
            if len(tok) >= 4 and tok not in ignored_tokens and tok in query_lower:
                return b
    return None


def _get_staff_presence_data(u, now, today_start, today_end):
    """
    Evaluates real-time presence, availability, and device connection for a staff member.
    """
    on_duty = getattr(u, 'is_on_duty', True)
    
    # 1. Device Connection Heartbeat
    call_device = getattr(u, 'call_device', None) if hasattr(u, 'call_device') else None
    if not call_device and CallDevice is not None:
        call_device = CallDevice.objects.filter(user=u).first()
        
    device_online = False
    device_last_seen = "No device registered"
    battery_info = None

    if call_device and call_device.last_seen_at:
        diff_secs = (now - call_device.last_seen_at).total_seconds()
        if diff_secs <= 300: # within 5 min
            device_online = True
            device_last_seen = "Phone Connected (Active now)"
        elif diff_secs <= 3600:
            device_last_seen = f"Phone seen {int(diff_secs // 60)}m ago"
        elif diff_secs <= 86400:
            device_last_seen = f"Phone seen {int(diff_secs // 3600)}h ago"
        else:
            days = int(diff_secs // 86400)
            device_last_seen = f"Phone seen {days}d ago"

        if hasattr(call_device, 'battery_percent') and call_device.battery_percent is not None:
            battery_info = f"{call_device.battery_percent}%"

    # 2. Login Activity
    logged_in_today = False
    last_login_str = "Never"
    if u.last_login:
        if u.last_login >= today_start:
            logged_in_today = True
            last_login_str = f"Today at {u.last_login.strftime('%I:%M %p')}"
        else:
            days_ago = (now.date() - u.last_login.date()).days
            last_login_str = f"{days_ago}d ago"

    # 3. Overall Presence & Availability
    is_present = (device_online or logged_in_today)
    
    if not u.is_active:
        presence_label = "Account Inactive"
        presence_badge = "secondary"
        avail_label = "Deactivated"
        avail_badge = "secondary"
    else:
        if is_present:
            presence_label = "Present"
            presence_badge = "success"
        else:
            presence_label = "Offline / Absent"
            presence_badge = "warning"

        if on_duty:
            avail_label = "Available (On-Duty)"
            avail_badge = "success"
        else:
            avail_label = "Unavailable (Off-Duty)"
            avail_badge = "warning"

    # 4. Calls & Follow-ups activity
    calls_count = 0
    if CallHistory is not None:
        calls_count = CallHistory.objects.filter(caller=u, created_at__range=(today_start, today_end)).count()

    followups_count = 0
    if FollowUp is not None:
        followups_count = FollowUp.objects.filter(
            Q(telecaller=u) | Q(assigned_user=u),
            follow_up_date=now.date(),
            status='Pending'
        ).count()

    return {
        'is_present': is_present,
        'presence_label': presence_label,
        'presence_badge': presence_badge,
        'is_available': on_duty and u.is_active,
        'avail_label': avail_label,
        'avail_badge': avail_badge,
        'device_online': device_online,
        'device_status': device_last_seen,
        'last_login_str': last_login_str,
        'battery': battery_info,
        'calls_today': calls_count,
        'pending_followups': followups_count
    }


def _format_lead_stats_card(leads_qs, label_prefix=""):
    """Builds standard metrics breakdown for a lead queryset."""
    total = leads_qs.count()
    status_counts = dict(leads_qs.values_list('status').annotate(c=Count('id')))

    converted = status_counts.get(LeadStatus.CONVERTED, 0)
    interested = status_counts.get(LeadStatus.INTERESTED, 0)
    contacted = status_counts.get(LeadStatus.CONTACTED, 0)
    follow_up = status_counts.get(LeadStatus.FOLLOW_UP, 0)
    lost = status_counts.get(LeadStatus.LOST, 0)

    conv_rate = round((converted / total * 100), 1) if total > 0 else 0.0

    return {
        'total': total,
        'converted': converted,
        'interested': interested,
        'contacted': contacted,
        'follow_up': follow_up,
        'lost': lost,
        'conv_rate': conv_rate,
        'chips': [
            {'label': 'Total Leads', 'value': total, 'badge': 'primary'},
            {'label': 'Converted', 'value': converted, 'badge': 'success'},
            {'label': 'Interested', 'value': interested, 'badge': 'info'},
            {'label': 'Follow-Up', 'value': follow_up, 'badge': 'warning'},
            {'label': 'Conversion Rate', 'value': f"{conv_rate}%", 'badge': 'success' if conv_rate >= 15 else 'secondary'},
        ]
    }


def process_superadmin_query(user, query_text):
    """
    Main rule-based NLP parser.
    Zero external APIs. Deterministic, fast, secure.
    """
    q = query_text.strip().lower()
    
    # -------------------------------------------------------------
    # 1. GREETING & GENERAL HELP
    # -------------------------------------------------------------
    if q in ['hi', 'hello', 'hey', 'help', 'menu', 'commands', 'what can you do', 'options']:
        return {
            'title': 'Welcome, Superadmin!',
            'text': (
                "I am your **TechPanda CRM Superadmin Assistant**, operating 100% locally on your server with live database access.\n\n"
                "**Here is what you can ask me anytime:**\n"
                "• **Live Lead Analytics:** *'How many leads today?'*, *'Leads this month'*, *'Conversion rate'*\n"
                "• **Branch Performance:** *'Leads in Anna Nagar'*, *'Branches list'*, *'T Nagar counselors'*\n"
                "• **Staff & Telecallers:** *'Unassigned telecallers'*, *'Top telecaller'*, *'Total counselors'*\n"
                "• **System Integrity & Health:** *'Is lead setup valid?'*, *'Duplicate leads'*, *'Pending follow-ups'*\n"
                "• **Financial Stats:** *'Total collections'*, *'Enrollments this month'*\n"
                "• **Deep Record Finder:** *'Find 9884012345'*, *'Lead Rajesh'*, *'Staff Anitha'*\n"
                "• **CRM How-To Guides:** *'How to add branch'*, *'How does centralized allocation work'*."
            ),
            'chips': [
                {'label': 'Engine', 'value': 'Local / Offline', 'badge': 'success'},
                {'label': 'Access', 'value': 'Superadmin Exclusive', 'badge': 'primary'},
                {'label': 'Latency', 'value': '&lt; 15ms', 'badge': 'info'}
            ],
            'actions': [
                {'label': 'Open Dashboard', 'url': '/admin/', 'icon': 'home'},
                {'label': 'Lead Allocation Setup', 'url': '/admin/settings/lead-setup/', 'icon': 'settings'}
            ],
            'suggestions': [
                "How many leads today?",
                "How many unassigned telecallers?",
                "Is lead allocation setup valid?",
                "Show all active branches",
                "How to bulk assign telecallers"
            ]
        }

    # -------------------------------------------------------------
    # 2. STAFF PRESENCE & AVAILABILITY (WHO IS PRESENT / ONLINE / AVAILABLE)
    # -------------------------------------------------------------
    now = timezone.now()
    today_start = timezone.make_aware(datetime.combine(now.date(), time.min))
    today_end = timezone.make_aware(datetime.combine(now.date(), time.max))



    # B. General presence: "who is present", "who is online", "staff attendance", "who is logged in"
    if 'who is present' in q or 'who is online' in q or 'attendance' in q or 'staff presence' in q or 'logged in today' in q:
        staff_qs = User.objects.filter(
            role__in=[UserRole.TELECALLER, UserRole.COUNSELOR, UserRole.BRANCH_HEAD, UserRole.SALES_HEAD],
            is_active=True
        ).select_related('branch').order_by('role', 'first_name', 'username')

        present_list = []
        offline_list = []

        for st in staff_qs:
            pdata = _get_staff_presence_data(st, now, today_start, today_end)
            st_name = st.get_full_name() or st.username
            st_branch = st.branch.name if st.branch else "All"
            duty_tag = "On-Duty" if pdata['is_available'] else "Off-Duty"

            if pdata['is_present']:
                detail = "Phone Online" if pdata['device_online'] else pdata['last_login_str']
                present_list.append(f"• **{st_name}** ({st.role}, *{st_branch}*) &mdash; `{duty_tag}` | {detail}")
            else:
                offline_list.append(f"• **{st_name}** ({st.role}, *{st_branch}*) &mdash; Last login: {pdata['last_login_str']}")

        text_sections = [
            f"**Present Staff Members ({len(present_list)} of {staff_qs.count()} Active Staff):**"
        ]
        if present_list:
            text_sections.extend(present_list[:12])
            if len(present_list) > 12:
                text_sections.append(f"*...and {len(present_list) - 12} more present staff.*")
        else:
            text_sections.append("• *No staff members currently online or logged in today.*")

        if offline_list:
            text_sections.append(f"\n**Offline / Absent Staff ({len(offline_list)}):**")
            text_sections.extend(offline_list[:6])
            if len(offline_list) > 6:
                text_sections.append(f"*...and {len(offline_list) - 6} more offline staff.*")

        return {
            'title': f"Staff Presence & Attendance ({len(present_list)}/{staff_qs.count()} Present)",
            'text': "\n".join(text_sections),
            'chips': [
                {'label': 'Present Today', 'value': len(present_list), 'badge': 'success'},
                {'label': 'Offline / Absent', 'value': len(offline_list), 'badge': 'warning' if len(offline_list) > 0 else 'success'},
                {'label': 'Total Staff', 'value': staff_qs.count(), 'badge': 'info'}
            ],
            'actions': [
                {'label': 'Staff Directory', 'url': '/admin/users/', 'icon': 'users'},
                {'label': 'Telecallers List', 'url': '/admin/telecallers/', 'icon': 'phone'}
            ],
            'suggestions': [
                "Who is available for leads?",
                "How many unassigned telecallers?",
                "Top telecaller this month"
            ]
        }

    # C. Available / On-duty staff: "who is available", "available telecallers", "who is on duty", "who is off duty"
    if 'who is available' in q or 'available telecaller' in q or 'on duty' in q or 'off duty' in q:
        all_tcs = User.objects.filter(role=UserRole.TELECALLER, is_active=True).select_related('branch', 'counselor')
        
        on_duty_tcs = []
        off_duty_tcs = []

        for tc in all_tcs:
            tc_name = tc.get_full_name() or tc.username
            tc_branch = tc.branch.name if tc.branch else "No Branch"
            tc_on_duty = getattr(tc, 'is_on_duty', True)
            
            pdata = _get_staff_presence_data(tc, now, today_start, today_end)
            pres_tag = "Present" if pdata['is_present'] else "Offline"

            if tc_on_duty:
                on_duty_tcs.append(f"• **{tc_name}** (*{tc_branch}*) &mdash; `{pres_tag}` | {pdata['calls_today']} calls today")
            else:
                off_duty_tcs.append(f"• **{tc_name}** (*{tc_branch}*) &mdash; `{pres_tag}` (Paused from lead allocation)")

        text_sections = [
            f"**Available Telecallers for Automated Lead Allocation ({len(on_duty_tcs)} of {all_tcs.count()}):**"
        ]
        if on_duty_tcs:
            text_sections.extend(on_duty_tcs[:10])
            if len(on_duty_tcs) > 10:
                text_sections.append(f"*...and {len(on_duty_tcs) - 10} more on-duty telecallers.*")
        else:
            text_sections.append("• *No telecallers currently marked on-duty.*")

        if off_duty_tcs:
            text_sections.append(f"\n**Off-Duty Telecallers ({len(off_duty_tcs)}):**")
            text_sections.extend(off_duty_tcs[:6])
            if len(off_duty_tcs) > 6:
                text_sections.append(f"*...and {len(off_duty_tcs) - 6} more off-duty telecallers.*")

        return {
            'title': f"Telecaller Lead Allocation Availability ({len(on_duty_tcs)} Available)",
            'text': "\n".join(text_sections),
            'chips': [
                {'label': 'Available (On-Duty)', 'value': len(on_duty_tcs), 'badge': 'success'},
                {'label': 'Off-Duty (Paused)', 'value': len(off_duty_tcs), 'badge': 'warning' if len(off_duty_tcs) > 0 else 'secondary'},
                {'label': 'Total Telecallers', 'value': all_tcs.count(), 'badge': 'info'}
            ],
            'actions': [
                {'label': 'Telecallers List', 'url': '/admin/telecallers/', 'icon': 'users'},
                {'label': 'Lead Allocation Setup', 'url': '/admin/settings/lead-setup/', 'icon': 'settings'}
            ],
            'suggestions': [
                "Who is present today?",
                "How many unassigned telecallers?",
                "Is lead allocation setup valid?"
            ]
        }

    # C. Specific user presence check: "is anitha present", "is anitha available", "is anitha online", "anitha presence"
    stop_words = {'who', 'is', 'are', 'the', 'all', 'any', 'user', 'staff', 'telecaller', 'telecallers', 'counselor', 'counselors', 'someone', 'every', 'everyone', 'what', 'which', 'how', 'many', 'today'}
    user_presence_match = re.search(r'\bis\s+([a-zA-Z0-9_\.\-]+)\s+(?:present|available|online|on duty|on-duty)', q)
    if not user_presence_match:
        user_presence_match = re.search(r'([a-zA-Z0-9_\.\-]+)\s+(?:present|available|online|on duty|on-duty)', q)
    user_presence_alt = re.search(r'(?:presence|availability)\s+(?:of\s+)?([a-zA-Z0-9_\.\-]+)', q)
    target_username = None
    if user_presence_match:
        cand = user_presence_match.group(1).strip()
        if cand not in stop_words and len(cand) >= 2:
            target_username = cand
    elif user_presence_alt:
        cand = user_presence_alt.group(1).strip()
        if cand not in stop_words and len(cand) >= 2:
            target_username = cand

    if target_username:
        matched_user = User.objects.filter(
            Q(username__iexact=target_username) |
            Q(first_name__iexact=target_username) |
            Q(last_name__iexact=target_username)
        ).select_related('branch').first()

        if not matched_user and len(target_username) >= 3:
            matched_user = User.objects.filter(
                Q(username__icontains=target_username) |
                Q(first_name__icontains=target_username) |
                Q(last_name__icontains=target_username)
            ).select_related('branch').first()

        if matched_user:
            pdata = _get_staff_presence_data(matched_user, now, today_start, today_end)
            u_name = matched_user.get_full_name() or matched_user.username
            u_role = matched_user.get_role_display() if hasattr(matched_user, 'get_role_display') else matched_user.role
            u_branch = matched_user.branch.name if matched_user.branch else "Organization-wide"

            battery_txt = f" | Battery: {pdata['battery']}" if pdata['battery'] else ""

            return {
                'title': f"Presence & Availability: {u_name}",
                'text': (
                    f"**Staff Member:** **{u_name}** ({u_role} &mdash; *{u_branch}*)\n\n"
                    f"• **Presence Status:** `{pdata['presence_label']}` (Last Login: {pdata['last_login_str']})\n"
                    f"• **Lead Assignment Availability:** `{pdata['avail_label']}`\n"
                    f"• **CallSync Companion Phone:** {pdata['device_status']}{battery_txt}\n"
                    f"• **Today's Activity:** **{pdata['calls_today']}** call(s) conducted | **{pdata['pending_followups']}** pending follow-up(s)"
                ),
                'chips': [
                    {'label': 'Presence', 'value': pdata['presence_label'], 'badge': pdata['presence_badge']},
                    {'label': 'Lead Allocation', 'value': pdata['avail_label'], 'badge': pdata['avail_badge']},
                    {'label': 'Calls Today', 'value': pdata['calls_today'], 'badge': 'info'}
                ],
                'actions': [
                    {'label': f"View {u_name} in Users", 'url': f"/admin/users/?q={matched_user.username}", 'icon': 'user'}
                ],
                'suggestions': [
                    "Who is present today?",
                    "Who is available for leads?",
                    "How many unassigned telecallers?"
                ]
            }

    # -------------------------------------------------------------
    # 3. DEEP RECORD FINDER: PHONE OR NAME SEARCH
    # -------------------------------------------------------------
    # Check if query contains a 10-digit phone number or "find <text>"
    phone_match = re.search(r'\b\d{10}\b', q)
    if phone_match or q.startswith('find ') or q.startswith('search ') or q.startswith('lead '):
        search_term = phone_match.group(0) if phone_match else re.sub(r'^(find|search|lead)\s+', '', q).strip()
        if len(search_term) >= 3:
            matched_leads = Lead.objects.filter(
                Q(phone__icontains=search_term) |
                Q(name__icontains=search_term) |
                Q(email__icontains=search_term)
            ).select_related('branch', 'assigned_telecaller', 'assigned_counselor')[:5]

            matched_users = User.objects.filter(
                Q(username__icontains=search_term) |
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(phone__icontains=search_term)
            ).select_related('branch')[:3]

            if matched_leads.exists() or matched_users.exists():
                text_lines = [f"Found records matching **'{search_term}'**:"]
                actions = []

                if matched_leads.exists():
                    text_lines.append("\n**Matched Leads:**")
                    for lead in matched_leads:
                        tc_name = lead.assigned_telecaller.get_full_name() if lead.assigned_telecaller else "Unassigned"
                        br_name = lead.branch.name if lead.branch else "No Branch"
                        text_lines.append(
                            f"• **{lead.name}** ({lead.phone}) &mdash; "
                            f"Status: `{lead.status}` | Branch: *{br_name}* | Telecaller: *{tc_name}*"
                        )
                        actions.append({
                            'label': f"View {lead.name or lead.phone}",
                            'url': f"/admin/leads/?q={lead.phone}",
                            'icon': 'user'
                        })

                if matched_users.exists():
                    text_lines.append("\n**Matched Staff Members:**")
                    for u in matched_users:
                        u_branch = u.branch.name if u.branch else "Organization-wide"
                        text_lines.append(
                            f"• **{u.get_full_name() or u.username}** &mdash; Role: `{u.role}` | Branch: *{u_branch}* | Active: `{u.is_active}`"
                        )

                return {
                    'title': f"Search Results for '{search_term}'",
                    'text': "\n".join(text_lines),
                    'chips': [
                        {'label': 'Leads Found', 'value': matched_leads.count(), 'badge': 'primary'},
                        {'label': 'Staff Found', 'value': matched_users.count(), 'badge': 'info'}
                    ],
                    'actions': actions[:3],
                    'suggestions': ["Show all leads today", "Unassigned telecallers", "System health"]
                }
            else:
                return {
                    'title': f"No Records Found for '{search_term}'",
                    'text': f"No student lead or staff user found matching **'{search_term}'** in the CRM database.",
                    'suggestions': ["How many leads today?", "Show active branches", "Unassigned telecallers"]
                }

    # -------------------------------------------------------------
    # 3. UNASSIGNED TELECALLERS
    # -------------------------------------------------------------
    if 'unassigned telecaller' in q or ('unassigned' in q and 'staff' in q) or 'without counselor' in q:
        unassigned_tcs = User.objects.filter(role=UserRole.TELECALLER, counselor__isnull=True, is_active=True)
        count = unassigned_tcs.count()
        
        tc_names = [u.get_full_name() or u.username for u in unassigned_tcs[:6]]
        tc_display = ", ".join(tc_names) if tc_names else "None"
        if count > 6:
            tc_display += f" and {count - 6} more..."

        return {
            'title': 'Unassigned Telecallers Status',
            'text': (
                f"There {'is' if count == 1 else 'are'} currently **{count} active telecaller{'s' if count != 1 else ''}** "
                f"not assigned to any counselor.\n\n"
                f"**Agents:** {tc_display}\n\n"
                f"*Tip: Unassigned telecallers are safely skipped by automatic lead distribution until assigned to a counselor or branch.*"
            ),
            'chips': [
                {'label': 'Unassigned Telecallers', 'value': count, 'badge': 'warning' if count > 0 else 'success'},
                {'label': 'Total Active Telecallers', 'value': User.objects.filter(role=UserRole.TELECALLER, is_active=True).count(), 'badge': 'info'}
            ],
            'actions': [
                {'label': 'Assign via Bulk Action Bar', 'url': '/admin/telecallers/?counselor=unassigned', 'icon': 'users'}
            ],
            'suggestions': [
                "How to bulk assign telecallers",
                "How many total counselors?",
                "Is lead allocation setup valid?"
            ]
        }

    # -------------------------------------------------------------
    # CAPABILITY C: LEAD BACKLOG & RESPONSE-TIME ALERTS
    # -------------------------------------------------------------
    # C1. Overloaded telecallers / pending backlog
    if 'overloaded telecaller' in q or 'telecaller backlog' in q or 'most leads pending' in q or 'overloaded staff' in q:
        pending_qs = Lead.objects.filter(
            assigned_telecaller__isnull=False,
            assigned_telecaller__is_active=True,
            status__in=[LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.INTERESTED, LeadStatus.FOLLOW_UP]
        ).values(
            'assigned_telecaller_id', 'assigned_telecaller__first_name',
            'assigned_telecaller__last_name', 'assigned_telecaller__username',
            'assigned_telecaller__branch__name'
        ).annotate(pending_count=Count('id')).order_by('-pending_count')[:6]

        if pending_qs:
            lines = ["**Telecallers with Highest Pending Lead Backlog:**\n"]
            for idx, item in enumerate(pending_qs, start=1):
                fname = item['assigned_telecaller__first_name'] or ""
                lname = item['assigned_telecaller__last_name'] or ""
                name = f"{fname} {lname}".strip() or item['assigned_telecaller__username']
                branch_label = item['assigned_telecaller__branch__name'] or "Organization-wide"
                lines.append(f"{idx}. **{name}** (*{branch_label}*): **{item['pending_count']}** pending leads")

            highest_val = pending_qs[0]['pending_count']
            return {
                'title': 'Telecaller Lead Backlog Monitor',
                'text': "\n".join(lines) + "\n\n*Tip: Rebalance leads across unassigned or available on-duty telecallers to maintain quick student response times.*",
                'chips': [
                    {'label': 'Highest Backlog', 'value': f"{highest_val} leads", 'badge': 'warning' if highest_val > 30 else 'info'},
                    {'label': 'Agents Tracked', 'value': len(pending_qs), 'badge': 'secondary'}
                ],
                'actions': [
                    {'label': 'Telecallers List', 'url': '/admin/telecallers/', 'icon': 'users'},
                    {'label': 'Lead Allocation Setup', 'url': '/admin/settings/lead-setup/', 'icon': 'sliders'}
                ],
                'suggestions': [
                    "Who is available for leads?",
                    "How many uncalled leads?",
                    "How many unassigned telecallers?"
                ]
            }
        else:
            return {
                'title': 'Telecaller Lead Backlog Monitor',
                'text': "All telecallers currently have zero pending or open leads. The pipeline is completely clear!",
                'chips': [
                    {'label': 'Pending Backlog', 'value': 0, 'badge': 'success'}
                ],
                'suggestions': ["How many leads today?", "Who is available for leads?"]
            }

    # C2. Uncalled / Fresh waiting leads or Backlog by branch
    if 'uncalled' in q or 'uncontacted' in q or 'waiting lead' in q or 'fresh lead' in q or 'lead backlog' in q or 'backlog by branch' in q:
        uncalled_qs = Lead.objects.filter(status=LeadStatus.NEW)
        total_uncalled = uncalled_qs.count()

        one_hour_ago = now - timedelta(hours=1)
        stale_qs = uncalled_qs.filter(created_at__lte=one_hour_ago)
        stale_count = stale_qs.count()

        # Branch breakdown
        branch_counts = uncalled_qs.values('branch__name').annotate(cnt=Count('id')).order_by('-cnt')
        branch_lines = []
        for b in branch_counts[:5]:
            b_name = b['branch__name'] or "Centralized (All Branches)"
            branch_lines.append(f"• **{b_name}**: **{b['cnt']}** uncalled")

        # Oldest uncalled sample
        oldest_samples = []
        for lead in stale_qs.select_related('branch', 'assigned_telecaller').order_by('created_at')[:4]:
            tc_name = lead.assigned_telecaller.get_full_name() if lead.assigned_telecaller else "Unassigned"
            br_name = lead.branch.name if lead.branch else "Centralized"
            wait_hours = int((now - lead.created_at).total_seconds() // 3600)
            wait_mins = int(((now - lead.created_at).total_seconds() % 3600) // 60)
            wait_str = f"{wait_hours}h {wait_mins}m" if wait_hours > 0 else f"{wait_mins}m"
            oldest_samples.append(f"• **{lead.name}** ({lead.phone}) &mdash; *{br_name}* | Wait: `{wait_str}` | Agent: *{tc_name}*")

        sections = [
            f"There {'is' if total_uncalled == 1 else 'are'} currently **{total_uncalled} uncalled / fresh lead{'s' if total_uncalled != 1 else ''}** in the system.",
            f"• **Waiting > 1 Hour:** **{stale_count}** lead{'s' if stale_count != 1 else ''}"
        ]

        if branch_lines:
            sections.append("\n**Backlog by Branch:**")
            sections.extend(branch_lines)

        if oldest_samples:
            sections.append("\n**Oldest Waiting Leads:**")
            sections.extend(oldest_samples)

        return {
            'title': f"Uncalled Leads & Response-Time Alert ({total_uncalled} Pending)",
            'text': "\n".join(sections),
            'chips': [
                {'label': 'Total Uncalled', 'value': total_uncalled, 'badge': 'warning' if total_uncalled > 0 else 'success'},
                {'label': 'Waiting > 1 Hr', 'value': stale_count, 'badge': 'danger' if stale_count > 0 else 'success'}
            ],
            'actions': [
                {'label': 'View Uncalled Leads', 'url': '/admin/leads/?status=New', 'icon': 'phone'},
                {'label': 'Lead Allocation Setup', 'url': '/admin/settings/lead-setup/', 'icon': 'sliders'}
            ],
            'suggestions': [
                "Overloaded telecallers",
                "Who is available for leads?",
                "How many unassigned telecallers?"
            ]
        }

    # -------------------------------------------------------------
    # CAPABILITY D: COUNSELOR DESK & WALK-IN VISITS
    # -------------------------------------------------------------
    # D1. Available counselors / Counselor desk
    if 'available counselor' in q or 'counselor desk' in q or 'counselors on duty' in q or ('counselor' in q and 'available' in q):
        counselors = User.objects.filter(role=UserRole.COUNSELOR, is_active=True).select_related('branch')
        avail_list = []
        busy_list = []

        for c in counselors:
            c_name = c.get_full_name() or c.username
            b_name = c.branch.name if c.branch else "All Branches"
            pdata = _get_staff_presence_data(c, now, today_start, today_end)
            
            # Active visits assigned
            active_visits = Lead.objects.filter(
                assigned_counselor=c,
                status__in=['Institute Visit', 'Visit Scheduled', 'Counseling']
            ).count()

            if pdata['is_present'] and pdata['is_available']:
                avail_list.append(f"• **{c_name}** (*{b_name}*) &mdash; `Ready` | {active_visits} active consultation(s)")
            else:
                status_note = pdata['presence_label'] if not pdata['is_present'] else "Off-Duty"
                busy_list.append(f"• **{c_name}** (*{b_name}*) &mdash; `{status_note}`")

        text_lines = [
            f"**Counselor Desk Availability ({len(avail_list)} of {counselors.count()} Ready):**"
        ]
        if avail_list:
            text_lines.extend(avail_list)
        else:
            text_lines.append("• *No counselors currently on duty and logged in.*")

        if busy_list:
            text_lines.append(f"\n**Offline / Off-Duty Counselors ({len(busy_list)}):**")
            text_lines.extend(busy_list[:5])

        return {
            'title': f"Counselor Desk Availability ({len(avail_list)} Ready)",
            'text': "\n".join(text_lines),
            'chips': [
                {'label': 'Counselors Ready', 'value': len(avail_list), 'badge': 'success' if len(avail_list) > 0 else 'warning'},
                {'label': 'Total Counselors', 'value': counselors.count(), 'badge': 'info'}
            ],
            'actions': [
                {'label': 'Users Directory', 'url': '/admin/users/?role=Counselor', 'icon': 'users'},
                {'label': 'Walk-In Leads', 'url': '/admin/leads/?source=Walk-in', 'icon': 'user-check'}
            ],
            'suggestions': [
                "Walk-in visits today",
                "Top counselor this month",
                "Who is present today?"
            ]
        }

    # D2. Scheduled walk-in / campus visits
    if 'walk in' in q or 'walk-in' in q or 'visit' in q or 'campus visit' in q or 'center visit' in q:
        today_date = now.date()
        visits_qs = Lead.objects.filter(
            Q(center_visit_date__date=today_date) |
            Q(status__in=['Institute Visit', 'Visit Scheduled', 'Visited', 'Counseling']) |
            Q(source='Walk-in')
        ).select_related('branch', 'assigned_counselor')

        today_scheduled = visits_qs.filter(center_visit_date__date=today_date).count()
        total_visits_pipeline = visits_qs.count()

        visit_samples = []
        for v in visits_qs.order_by('-updated_at')[:6]:
            c_name = v.assigned_counselor.get_full_name() if v.assigned_counselor else "Unassigned Counselor"
            b_name = v.branch.name if v.branch else "Organization-wide"
            tok = f" | Token #{v.token_number}" if v.token_number else ""
            visit_samples.append(
                f"• **{v.name}** ({v.phone}) &mdash; Status: `{v.status}` | *{b_name}* | Counselor: *{c_name}*{tok}"
            )

        text_lines = [
            f"**Campus & Center Walk-In Visits Overview:**",
            f"• **Visits Scheduled for Today:** **{today_scheduled}** student(s)",
            f"• **Total in Visit / Counseling Pipeline:** **{total_visits_pipeline}** lead(s)"
        ]
        if visit_samples:
            text_lines.append("\n**Recent / Scheduled Visits:**")
            text_lines.extend(visit_samples)

        return {
            'title': f"Walk-In & Center Visits Desk ({today_scheduled} Today)",
            'text': "\n".join(text_lines),
            'chips': [
                {'label': 'Visits Today', 'value': today_scheduled, 'badge': 'success' if today_scheduled > 0 else 'info'},
                {'label': 'Visit Pipeline', 'value': total_visits_pipeline, 'badge': 'primary'}
            ],
            'actions': [
                {'label': 'View Walk-In Leads', 'url': '/admin/leads/?source=Walk-in', 'icon': 'users'},
                {'label': 'Lead Allocation Setup', 'url': '/admin/settings/lead-setup/', 'icon': 'sliders'}
            ],
            'suggestions': [
                "Which counselors are available?",
                "Top counselor this month",
                "How many leads today?"
            ]
        }

    # D3. Top counselor / Counselor ranking
    if 'top counselor' in q or 'best counselor' in q or 'counselor ranking' in q or 'counselor performance' in q:
        dt_start, dt_end, range_label = _get_date_range(q)
        leads_qs = Lead.objects.filter(
            assigned_counselor__isnull=False,
            status__in=[LeadStatus.CONVERTED, 'Enrolled', 'Joined']
        )
        if dt_start and dt_end:
            leads_qs = leads_qs.filter(updated_at__range=(dt_start, dt_end))

        top_stats = leads_qs.values(
            'assigned_counselor_id', 'assigned_counselor__username',
            'assigned_counselor__first_name', 'assigned_counselor__last_name',
            'assigned_counselor__branch__name'
        ).annotate(conversions=Count('id')).order_by('-conversions')[:5]

        if top_stats:
            lines = []
            for idx, item in enumerate(top_stats, start=1):
                fname = item['assigned_counselor__first_name'] or ""
                lname = item['assigned_counselor__last_name'] or ""
                name = f"{fname} {lname}".strip() or item['assigned_counselor__username']
                br = item['assigned_counselor__branch__name'] or "Organization-wide"
                lines.append(f"{idx}. **{name}** (*{br}*): **{item['conversions']}** enrolled/converted")

            return {
                'title': f"Top Counselor Leaderboard ({range_label})",
                'text': "\n".join(lines),
                'chips': [
                    {'label': 'Top Conversions', 'value': top_stats[0]['conversions'], 'badge': 'success'},
                    {'label': 'Time Window', 'value': range_label, 'badge': 'info'}
                ],
                'actions': [
                    {'label': 'View Reports', 'url': '/admin/reports/', 'icon': 'bar-chart'}
                ],
                'suggestions': ["Which counselors are available?", "Walk-in visits today", "Top telecaller this month"]
            }
        else:
            return {
                'title': f"Counselor Conversions ({range_label})",
                'text': f"No counselor conversions recorded for timeframe **{range_label}**.",
                'suggestions': ["Which counselors are available?", "Walk-in visits today"]
            }

    # -------------------------------------------------------------
    # CAPABILITY E: SUPERADMIN SECURITY & AUDIT OPERATIONS
    # -------------------------------------------------------------
    # E1. Outside office hours logins
    if 'outside office hours' in q or 'after hours login' in q or 'late night login' in q or 'odd hours' in q or 'after hours' in q:
        after_hours_logins = []
        if Activity is not None:
            recent_logins = Activity.objects.filter(
                action='User Logged In',
                timestamp__gte=now - timedelta(days=7)
            ).select_related('user').order_by('-timestamp')

            for act in recent_logins:
                local_dt = timezone.localtime(act.timestamp)
                if local_dt.hour < 8 or local_dt.hour >= 20:
                    uname = act.user.get_full_name() if act.user else "Unknown User"
                    role = getattr(act.user, 'role', 'Staff')
                    ip = act.ip_address or "Local IP"
                    time_str = local_dt.strftime('%b %d, %I:%M %p')
                    after_hours_logins.append(f"• **{uname}** ({role}) &mdash; `{time_str}` (IP: `{ip}`)")

        if after_hours_logins:
            return {
                'title': f"Out-of-Hours Logins Audit ({len(after_hours_logins)} Flagged in Last 7 Days)",
                'text': (
                    "**Logins recorded outside standard office hours (before 08:00 AM or after 08:00 PM):**\n\n" +
                    "\n".join(after_hours_logins[:8])
                ),
                'chips': [
                    {'label': 'Out-of-Hours Logins', 'value': len(after_hours_logins), 'badge': 'warning'},
                    {'label': 'Audit Period', 'value': 'Last 7 Days', 'badge': 'info'}
                ],
                'actions': [
                    {'label': 'Users Directory', 'url': '/admin/users/', 'icon': 'shield'}
                ],
                'suggestions': ["Recent administrative actions", "Users created recently", "System health"]
            }
        else:
            return {
                'title': 'Out-of-Hours Logins Audit',
                'text': "No staff logins were detected outside standard office hours (08:00 AM &ndash; 08:00 PM) during the past 7 days. All access conforms to normal working hours.",
                'chips': [
                    {'label': 'Out-of-Hours Logins', 'value': 0, 'badge': 'success'},
                    {'label': 'Audit Period', 'value': 'Last 7 Days', 'badge': 'info'}
                ],
                'suggestions': ["Recent administrative actions", "Users created recently"]
            }

    # E2. Recent administrative audit trail
    if 'administrative action' in q or 'audit log' in q or 'recent audit' in q or 'system activity' in q or 'recent actions' in q:
        recent_acts = None
        if Activity is not None:
            recent_acts = Activity.objects.exclude(action__in=['User Logged In', 'User Logged Out']).order_by('-timestamp')[:8]
        
        if recent_acts and recent_acts.exists():
            audit_lines = []
            for a in recent_acts:
                local_dt = timezone.localtime(a.timestamp)
                time_str = local_dt.strftime('%b %d, %I:%M %p')
                u_str = a.user.username if a.user else "System"
                desc = a.description or a.action
                if len(desc) > 85:
                    desc = desc[:82] + "..."
                audit_lines.append(f"• **{a.action}** by *{u_str}* ({time_str})\n  &nbsp;&nbsp;`{desc}`")

            return {
                'title': 'Recent Administrative Audit Trail',
                'text': "**Latest System & Administrative Events:**\n\n" + "\n\n".join(audit_lines),
                'chips': [
                    {'label': 'Total Logged Events', 'value': Activity.objects.count() if Activity else 0, 'badge': 'info'},
                    {'label': 'Recent Entries Shown', 'value': min(recent_acts.count(), 8), 'badge': 'primary'}
                ],
                'actions': [
                    {'label': 'Admin Dashboard', 'url': '/admin/', 'icon': 'shield'},
                    {'label': 'Telecallers List', 'url': '/admin/telecallers/', 'icon': 'users'}
                ],
                'suggestions': [
                    "Users created recently",
                    "Who logged in outside office hours?",
                    "Is lead allocation setup valid?"
                ]
            }
        else:
            return {
                'title': 'Administrative Audit Trail',
                'text': "No administrative events have been recorded in the activity log yet.",
                'suggestions': ["How many leads today?", "System health"]
            }

    # E3. Users created recently / Staff changes
    if 'users created' in q or 'new users' in q or 'staff onboarded' in q or 'user changes' in q:
        seven_days_ago = now - timedelta(days=7)
        recent_users = User.objects.filter(created_at__gte=seven_days_ago).order_by('-created_at')
        
        if not recent_users.exists():
            # Check date_joined if created_at has none
            recent_users = User.objects.filter(date_joined__gte=seven_days_ago).order_by('-date_joined')

        if recent_users.exists():
            user_lines = []
            for u in recent_users[:8]:
                u_name = u.get_full_name() or u.username
                u_branch = u.branch.name if u.branch else "Organization-wide"
                date_val = u.created_at if u.created_at else u.date_joined
                local_dt = timezone.localtime(date_val)
                date_str = local_dt.strftime('%b %d, %Y')
                user_lines.append(f"• **{u_name}** &mdash; Role: `{u.role}` | Branch: *{u_branch}* | Added: `{date_str}`")

            return {
                'title': f"Staff Onboarded Recently ({recent_users.count()} in Last 7 Days)",
                'text': "**Staff members added to the CRM within the past 7 days:**\n\n" + "\n".join(user_lines),
                'chips': [
                    {'label': 'New Users (7 Days)', 'value': recent_users.count(), 'badge': 'success'},
                    {'label': 'Total Active Staff', 'value': User.objects.filter(is_active=True).count(), 'badge': 'info'}
                ],
                'actions': [
                    {'label': 'Users Directory', 'url': '/admin/users/', 'icon': 'users'}
                ],
                'suggestions': [
                    "Recent administrative actions",
                    "Who is present today?",
                    "How many unassigned telecallers?"
                ]
            }
        else:
            return {
                'title': 'Staff Onboarded Recently',
                'text': "No new user accounts were created in the past 7 days.",
                'chips': [
                    {'label': 'New Users (7 Days)', 'value': 0, 'badge': 'info'}
                ],
                'suggestions': ["How to add counselor", "Who is present today?"]
            }

    # -------------------------------------------------------------
    # 4. TOP TELECALLER / PERFORMERS
    # -------------------------------------------------------------
    if 'top telecaller' in q or 'best telecaller' in q or 'telecaller ranking' in q:
        dt_start, dt_end, range_label = _get_date_range(q)
        leads_qs = Lead.objects.filter(status=LeadStatus.CONVERTED)
        if dt_start and dt_end:
            leads_qs = leads_qs.filter(updated_at__range=(dt_start, dt_end))

        top_stats = leads_qs.values(
            'assigned_telecaller_id', 'assigned_telecaller__username',
            'assigned_telecaller__first_name', 'assigned_telecaller__last_name'
        ).annotate(conversions=Count('id')).order_by('-conversions')[:5]

        if top_stats:
            leader_board = []
            for idx, item in enumerate(top_stats, start=1):
                fname = item['assigned_telecaller__first_name'] or ""
                lname = item['assigned_telecaller__last_name'] or ""
                name = f"{fname} {lname}".strip() or item['assigned_telecaller__username'] or "Unassigned"
                leader_board.append(f"{idx}. **{name}**: **{item['conversions']}** converted leads")

            return {
                'title': f"Top Telecaller Leaderboard ({range_label})",
                'text': "\n".join(leader_board),
                'chips': [
                    {'label': 'Top Conversions', 'value': top_stats[0]['conversions'], 'badge': 'success'},
                    {'label': 'Time Window', 'value': range_label, 'badge': 'info'}
                ],
                'actions': [
                    {'label': 'View Telecaller Reports', 'url': '/admin/reports/', 'icon': 'bar-chart'}
                ],
                'suggestions': ["How many leads today?", "Unassigned telecallers", "Duplicate leads count"]
            }
        else:
            return {
                'title': f"Top Telecaller ({range_label})",
                'text': f"No conversions recorded for the timeframe: **{range_label}**.",
                'suggestions': ["Leads this month", "Unassigned telecallers", "Show all branches"]
            }

    # -------------------------------------------------------------
    # 5. ALLOCATION HEALTH & INTEGRITY CHECKS
    # -------------------------------------------------------------
    if 'setup valid' in q or 'allocation valid' in q or 'allocation 100' in q or 'system health' in q or 'audit' in q:
        invalid_items = []
        active_branches = Branch.objects.filter(status='Active')
        
        for br in active_branches:
            for src in CANONICAL_LEAD_SOURCES:
                total_pct = TelecallerLeadSetup.objects.filter(
                    branch=br, source=src, is_active=True
                ).aggregate(s=Sum('assignment_percentage'))['s'] or 0
                if total_pct > 0 and total_pct != 100:
                    invalid_items.append(f"• **{br.name}** &mdash; Source: `{src}` is at **{total_pct}%** (must be 100%)")

        duplicates_count = DuplicateLeadRecord.objects.count()
        unassigned_tcs_count = User.objects.filter(role=UserRole.TELECALLER, counselor__isnull=True, is_active=True).count()

        if not invalid_items:
            status_summary = (
                "**All configured lead allocation rules are healthy and set to 100%!**\n\n"
                f"• **Lead Allocation Status:** 100% Valid across all active configured pipelines.\n"
                f"• **Duplicate Records Flagged:** {duplicates_count} groups.\n"
                f"• **Unassigned Telecallers:** {unassigned_tcs_count} agents."
            )
            overall_badge = "success"
        else:
            status_summary = (
                f"**Notice: {len(invalid_items)} allocation rule(s) require adjustment to 100%:**\n\n" +
                "\n".join(invalid_items[:6])
            )
            overall_badge = "warning"

        return {
            'title': 'System & Lead Allocation Health Audit',
            'text': status_summary,
            'chips': [
                {'label': 'Allocation Health', 'value': 'Valid 100%' if not invalid_items else f'{len(invalid_items)} Incomplete', 'badge': overall_badge},
                {'label': 'Duplicate Groups', 'value': duplicates_count, 'badge': 'info' if duplicates_count == 0 else 'warning'},
                {'label': 'Unassigned Telecallers', 'value': unassigned_tcs_count, 'badge': 'secondary' if unassigned_tcs_count == 0 else 'warning'}
            ],
            'actions': [
                {'label': 'Manage Lead Setup', 'url': '/admin/settings/lead-setup/', 'icon': 'sliders'},
                {'label': 'View Duplicate Leads', 'url': '/admin/duplicate-leads/', 'icon': 'copy'}
            ],
            'suggestions': [
                "How many unassigned telecallers?",
                "How many leads today?",
                "How to bulk assign telecallers"
            ]
        }

    # -------------------------------------------------------------
    # 6. DUPLICATE LEADS COUNT
    # -------------------------------------------------------------
    if 'duplicate' in q:
        dup_count = DuplicateLeadRecord.objects.count()
        return {
            'title': 'Duplicate Leads Detection',
            'text': (
                f"The system has detected **{dup_count} duplicate lead cluster{'s' if dup_count != 1 else ''}**.\n\n"
                "Duplicates are grouped automatically when matching phone numbers or emails are ingested from multiple sources."
            ),
            'chips': [
                {'label': 'Duplicate Clusters', 'value': dup_count, 'badge': 'warning' if dup_count > 0 else 'success'}
            ],
            'actions': [
                {'label': 'Review & Merge Duplicates', 'url': '/admin/duplicate-leads/', 'icon': 'copy'}
            ],
            'suggestions': [
                "How many leads today?",
                "Is lead allocation setup valid?",
                "Unassigned telecallers"
            ]
        }

    # -------------------------------------------------------------
    # 7. KNOWLEDGE BASE & HOW-TO QUESTIONS
    # -------------------------------------------------------------
    for kb in CRM_KNOWLEDGE_BASE:
        for kw in kb['keywords']:
            if kw in q:
                return {
                    'title': kb['title'],
                    'text': kb['content'],
                    'chips': [
                        {'label': 'Guide Type', 'value': 'CRM SOP', 'badge': 'info'}
                    ],
                    'actions': [
                        {'label': kb['action']['label'], 'url': kb['action']['url'], 'icon': 'external-link'}
                    ],
                    'suggestions': [
                        "How many leads today?",
                        "How to add counselor",
                        "Centralized lead allocation hub",
                        "How to bulk assign telecallers"
                    ]
                }

    # -------------------------------------------------------------
    # 8. BRANCH SPECIFIC LEADS & PERFORMANCE
    # -------------------------------------------------------------
    matched_branch = _extract_branch(q)
    if matched_branch and ('lead' in q or 'branch' in q or 'performance' in q or 'telecaller' in q or 'counselor' in q):
        dt_start, dt_end, range_label = _get_date_range(q)
        branch_leads = Lead.objects.filter(branch=matched_branch)
        if dt_start and dt_end:
            branch_leads = branch_leads.filter(created_at__range=(dt_start, dt_end))

        stats = _format_lead_stats_card(branch_leads)
        tc_count = User.objects.filter(role=UserRole.TELECALLER, branch=matched_branch, is_active=True).count()
        co_count = User.objects.filter(role=UserRole.COUNSELOR, branch=matched_branch, is_active=True).count()

        return {
            'title': f"{matched_branch.name} Performance ({range_label})",
            'text': (
                f"**Branch Overview for {matched_branch.name}:**\n"
                f"• **Total Leads ({range_label}):** {stats['total']}\n"
                f"• **Converted:** {stats['converted']} ({stats['conv_rate']}%)\n"
                f"• **Interested / Follow-Up:** {stats['interested'] + stats['follow_up']}\n"
                f"• **Active Staff:** {co_count} Counselors, {tc_count} Telecallers."
            ),
            'chips': stats['chips'],
            'actions': [
                {'label': f"View {matched_branch.name} Leads", 'url': f"/admin/leads/?branch={matched_branch.id}", 'icon': 'list'},
                {'label': 'Configure Branch Lead Setup', 'url': f"/admin/settings/lead-setup/?branch_id={matched_branch.id}", 'icon': 'settings'}
            ],
            'suggestions': [
                "How many leads today?",
                "Unassigned telecallers",
                "Show all active branches"
            ]
        }

    # -------------------------------------------------------------
    # 8. GENERAL BRANCH LIST
    # -------------------------------------------------------------
    if 'branch list' in q or 'all branches' in q or 'branches count' in q or ('how many' in q and 'branch' in q):
        branches = Branch.objects.filter(status='Active').order_by('name')
        b_names = [f"• **{b.name}**" for b in branches]
        return {
            'title': f"Active Branches ({branches.count()} Total)",
            'text': "\n".join(b_names),
            'chips': [
                {'label': 'Active Branches', 'value': branches.count(), 'badge': 'primary'}
            ],
            'actions': [
                {'label': 'Branches Directory', 'url': '/admin/branches/', 'icon': 'map-pin'},
                {'label': 'Lead Allocation Setup', 'url': '/admin/settings/lead-setup/', 'icon': 'sliders'}
            ],
            'suggestions': [
                "How to add branch",
                "Leads in Anna Nagar",
                "How many leads today?"
            ]
        }

    # -------------------------------------------------------------
    # 9. GENERAL LEADS COUNT / STATUS QUERIES
    # -------------------------------------------------------------
    if 'lead' in q or 'conversion' in q or 'how many' in q:
        dt_start, dt_end, range_label = _get_date_range(q)
        leads_qs = Lead.objects.all()
        if dt_start and dt_end:
            leads_qs = leads_qs.filter(created_at__range=(dt_start, dt_end))

        stats = _format_lead_stats_card(leads_qs)
        
        return {
            'title': f"Organization Lead Statistics ({range_label})",
            'text': (
                f"**Lead Pipeline Summary for {range_label}:**\n"
                f"• **Total Ingested Leads:** **{stats['total']}**\n"
                f"• **Converted Students:** **{stats['converted']}** ({stats['conv_rate']}% conversion rate)\n"
                f"• **Currently Interested:** **{stats['interested']}**\n"
                f"• **Under Follow-Up:** **{stats['follow_up']}**\n"
                f"• **Contacted / In Progress:** **{stats['contacted']}**\n"
                f"• **Marked Lost:** **{stats['lost']}**"
            ),
            'chips': stats['chips'],
            'actions': [
                {'label': f"View {range_label} Leads", 'url': '/admin/leads/', 'icon': 'list'},
                {'label': 'Reports Dashboard', 'url': '/admin/reports/', 'icon': 'pie-chart'}
            ],
            'suggestions': [
                "Top telecaller this month",
                "How many unassigned telecallers?",
                "Is lead allocation setup valid?",
                "Show all active branches"
            ]
        }

    # -------------------------------------------------------------
    # 10. FINANCIAL & REVENUE STATS (ENROLLMENTS / TRANSACTIONS)
    # -------------------------------------------------------------
    if 'fee' in q or 'collection' in q or 'revenue' in q or 'finance' in q or 'payment' in q:
        dt_start, dt_end, range_label = _get_date_range(q)
        enroll_count = 0
        total_coll = 0
        
        if Enrollment is not None:
            eqs = Enrollment.objects.all()
            if dt_start and dt_end:
                eqs = eqs.filter(created_at__range=(dt_start, dt_end))
            enroll_count = eqs.count()

        if PaymentTransaction is not None:
            pqs = PaymentTransaction.objects.filter(status='Success')
            if dt_start and dt_end:
                pqs = pqs.filter(transaction_date__range=(dt_start, dt_end))
            total_coll = pqs.aggregate(s=Sum('amount'))['s'] or 0

        return {
            'title': f"Financial & Enrollment Summary ({range_label})",
            'text': (
                f"**Financial Overview for {range_label}:**\n"
                f"• **Total Students Enrolled:** **{enroll_count}**\n"
                f"• **Successful Fee Collections:** **₹{total_coll:,.2f}**"
            ),
            'chips': [
                {'label': 'Enrollments', 'value': enroll_count, 'badge': 'success'},
                {'label': 'Collections', 'value': f"₹{total_coll:,.0f}", 'badge': 'primary'},
                {'label': 'Period', 'value': range_label, 'badge': 'info'}
            ],
            'actions': [
                {'label': 'Open Finance Reports', 'url': '/admin/reports/', 'icon': 'credit-card'}
            ],
            'suggestions': [
                "How many leads today?",
                "Top telecaller this month",
                "Is lead allocation setup valid?"
            ]
        }

    # -------------------------------------------------------------
    # 12. FALLBACK WITH CLOSE MATCHES OR SUGGESTIONS
    # -------------------------------------------------------------
    all_kb_titles = [kb['title'] for kb in CRM_KNOWLEDGE_BASE]
    closest = get_close_matches(q, [kw for kb in CRM_KNOWLEDGE_BASE for kw in kb['keywords']], n=1, cutoff=0.5)
    
    hint_text = ""
    if closest:
        hint_text = f"\n\n*Did you mean to ask about:* **'{closest[0]}'**?"

    return {
        'title': 'Query Not Recognized',
        'text': (
            f"I didn't find a direct CRM metric or SOP matching **'{query_text}'**.{hint_text}\n\n"
            "Please try clicking one of the common actions below or type a specific CRM question:"
        ),
        'chips': [
            {'label': 'Scope', 'value': 'CRM Internal Data Only', 'badge': 'secondary'}
        ],
        'actions': [
            {'label': 'Admin Dashboard', 'url': '/admin/', 'icon': 'home'},
            {'label': 'Lead Allocation Setup', 'url': '/admin/settings/lead-setup/', 'icon': 'settings'}
        ],
        'suggestions': [
            "How many leads today?",
            "How many unassigned telecallers?",
            "Is lead allocation setup valid?",
            "Top telecaller this month",
            "How to add branch"
        ]
    }
