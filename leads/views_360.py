from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from leads.models import Lead
from activities.models import Activity
from leads.models_enrollment import Enrollment, PaymentTransaction
from chat.models import Conversation
from leads.duplicates import normalize_phone
from accounts.permissions import can_access_lead
import logging

logger = logging.getLogger(__name__)


@login_required
def lead_360_data(request, lead_id):
    """
    Unified 360-Degree Student Admissions Drawer endpoint.
    Aggregates Student Info, CallHistory, WhatsApp Chats, Payment Transactions,
    Enrollments, and Counselor Notes into a single chronological timeline.
    """
    user = request.user
    lead = get_object_or_404(
        Lead.objects.select_related('branch', 'assigned_counselor', 'assigned_telecaller', 'channel', 'product'),
        pk=lead_id
    )

    # Strict object-level access control across branches and assigned roles
    if not can_access_lead(user, lead):
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

    timeline = []

    # 1. Calls
    for c in lead.calls.select_related('caller', 'telecaller').order_by('-created_at')[:30]:
        t = getattr(c, 'call_started_at', None) or getattr(c, 'created_at', None)
        caller_name = (c.caller.get_full_name() or c.caller.username) if c.caller else (
            (c.telecaller.get_full_name() or c.telecaller.username) if getattr(c, 'telecaller', None) else 'Telecaller'
        )
        outcome = getattr(c, 'call_outcome', '') or getattr(c, 'outcome', 'Completed')
        dur = getattr(c, 'duration', 0) or 0
        dur_str = f"{dur // 60}m {dur % 60}s" if dur > 0 else "0s"
        rec_url = getattr(c, 'recording_url', '') or (c.recording.url if getattr(c, 'recording', None) else '')

        timeline.append({
            'timestamp': t.isoformat() if t else '',
            'display_time': t.strftime('%b %d, %Y %I:%M %p') if t else '',
            'type': 'call',
            'icon': 'phone',
            'color': '#0284c7',
            'bg_color': '#f0f9ff',
            'title': f"Call: {outcome}",
            'description': f"Duration: {dur_str} &bull; Caller: {caller_name}",
            'notes': c.notes or '',
            'recording_url': rec_url,
            'details': {
                'outcome': outcome,
                'duration': dur_str,
                'caller': caller_name
            }
        })

    # 2. WhatsApp Chats
    try:
        clean_p = normalize_phone(lead.phone)
        if clean_p:
            p_tail = clean_p[-10:] if len(clean_p) >= 10 else clean_p
            conv_qs = Conversation.objects.filter(
                Q(phone_number__endswith=p_tail) | Q(phone_number__icontains=clean_p)
            )
            for conv in conv_qs:
                for m in conv.messages.order_by('-timestamp')[:20]:
                    t = m.timestamp
                    sender = 'Student' if getattr(m, 'sender', '') == 'customer' else 'Counselor/AI'
                    timeline.append({
                        'timestamp': t.isoformat() if t else '',
                        'display_time': t.strftime('%b %d, %Y %I:%M %p') if t else '',
                        'type': 'whatsapp',
                        'icon': 'message-square',
                        'color': '#059669',
                        'bg_color': '#ecfdf5',
                        'title': f"WhatsApp from {sender}",
                        'description': (m.message_text or '')[:140] + ('...' if len(m.message_text or '') > 140 else ''),
                        'notes': m.message_text or '',
                        'recording_url': '',
                        'details': {
                            'sender_type': getattr(m, 'sender', ''),
                            'status': getattr(m, 'status', 'delivered')
                        }
                    })
    except Exception as e:
        logger.warning("Error loading 360 WhatsApp messages: %s", e)

    # 3. Payments & Enrollment
    total_paid = 0
    total_payable = 0
    enrollment_number = ''
    enrollment_status = 'Not Enrolled'

    try:
        enr = getattr(lead, 'enrollment', None)
        if enr:
            enrollment_number = enr.enrollment_number
            enrollment_status = enr.status
            total_payable = float(enr.total_payable)
            total_paid = float(enr.total_paid)

            timeline.append({
                'timestamp': enr.created_at.isoformat() if getattr(enr, 'created_at', None) else '',
                'display_time': enr.created_at.strftime('%b %d, %Y %I:%M %p') if getattr(enr, 'created_at', None) else '',
                'type': 'enrollment',
                'icon': 'award',
                'color': '#7c3aed',
                'bg_color': '#f5f3ff',
                'title': f"Enrolled: {enr.enrollment_number}",
                'description': f"Program: {enr.product.name if enr.product else 'Course'} &bull; Plan: {enr.payment_plan}",
                'notes': f"Total Fee: ₹{total_payable:,.2f} &bull; Status: {enr.payment_status}",
                'recording_url': '',
                'details': {
                    'enrollment_number': enr.enrollment_number,
                    'plan': enr.payment_plan,
                    'status': enr.status
                }
            })

            # Transactions / Payments
            for tx in enr.payments.order_by('-payment_date'):
                t = getattr(tx, 'payment_date', None) or tx.created_at
                timeline.append({
                    'timestamp': t.isoformat() if t else '',
                    'display_time': t.strftime('%b %d, %Y %I:%M %p') if t else '',
                    'type': 'payment',
                    'icon': 'credit-card',
                    'color': '#16a34a' if tx.status == 'Approved' else '#d97706',
                    'bg_color': '#f0fdf4' if tx.status == 'Approved' else '#fffbeb',
                    'title': f"Payment ₹{tx.amount:,.2f} ({tx.status})",
                    'description': f"Method: {tx.payment_method} &bull; Ref/UTR: {tx.transaction_reference or 'N/A'}",
                    'notes': f"Receipt: {tx.receipt_number or 'Pending'} &bull; Verified: {tx.status}",
                    'recording_url': '',
                    'details': {
                        'amount': float(tx.amount),
                        'method': tx.payment_method,
                        'reference': tx.transaction_reference,
                        'receipt_number': tx.receipt_number,
                        'status': tx.status
                    }
                })
    except Exception as e:
        logger.warning("Error loading 360 payments: %s", e)

    # 4. Lead Status History
    for s in lead.status_history.select_related('changed_by').order_by('-created_at')[:15]:
        t = s.created_at
        changer = (s.changed_by.get_full_name() or s.changed_by.username) if s.changed_by else 'System'
        timeline.append({
            'timestamp': t.isoformat() if t else '',
            'display_time': t.strftime('%b %d, %Y %I:%M %p') if t else '',
            'type': 'status',
            'icon': 'activity',
            'color': '#475569',
            'bg_color': '#f8fafc',
            'title': f"Status: {s.old_status or 'Initial'} → {s.new_status}",
            'description': f"Updated by: {changer}",
            'notes': s.remarks or '',
            'recording_url': '',
            'details': {
                'old_status': s.old_status,
                'new_status': s.new_status,
                'changed_by': changer
            }
        })

    # 5. Lead Activities / Notes
    activities_qs = Activity.objects.filter(object_type='Lead', object_id=str(lead.id)).select_related('user').order_by('-timestamp')[:25]
    for act in activities_qs:
        t = act.timestamp
        performer = (act.user.get_full_name() or act.user.username) if act.user else 'System'
        is_sys = 'System' in (act.action or '') or not act.user
        timeline.append({
            'timestamp': t.isoformat() if t else '',
            'display_time': t.strftime('%b %d, %Y %I:%M %p') if t else '',
            'type': 'note',
            'icon': 'file-text',
            'color': '#64748b' if is_sys else '#0284c7',
            'bg_color': '#f8fafc' if is_sys else '#f0f9ff',
            'title': act.action or 'Note',
            'description': f"By: {performer}",
            'notes': act.description or '',
            'recording_url': '',
            'details': {
                'action': act.action,
                'performed_by': performer
            }
        })

    # 6. TeleCRM Historical Actions
    tc_mirror = lead.telecrm_mirrors.first()
    tc_call_count = 0
    if tc_mirror:
        tc_actions = tc_mirror.actions.order_by('-occurred_at')
        tc_call_count = tc_actions.filter(type__icontains='CALL').count()
        for tc_act in tc_actions[:40]:
            t = tc_act.occurred_at
            act_type = (tc_act.type or '').upper()
            if 'CALL' in act_type:
                dur_str = tc_act.display_duration
                outcome = tc_act.display_status or 'Call Event'
                timeline.append({
                    'timestamp': t.isoformat() if t else '',
                    'display_time': t.strftime('%b %d, %Y %I:%M %p') if t else '',
                    'type': 'call',
                    'icon': 'phone',
                    'color': '#0284c7',
                    'bg_color': '#f0f9ff',
                    'title': f"TeleCRM {act_type.replace('_', ' ').title()}: {outcome}",
                    'description': f"Duration: {dur_str} &bull; User: {tc_act.employee_uid or 'Telecaller'}",
                    'notes': tc_act.display_text or '',
                    'recording_url': '',
                    'details': {
                        'outcome': outcome,
                        'duration': dur_str,
                        'caller': tc_act.employee_uid
                    }
                })
            elif 'WHATSAPP' in act_type:
                timeline.append({
                    'timestamp': t.isoformat() if t else '',
                    'display_time': t.strftime('%b %d, %Y %I:%M %p') if t else '',
                    'type': 'whatsapp',
                    'icon': 'message-square',
                    'color': '#059669',
                    'bg_color': '#ecfdf5',
                    'title': f"TeleCRM {act_type.replace('_', ' ').title()}",
                    'description': (tc_act.display_text or '')[:140] + ('...' if len(tc_act.display_text or '') > 140 else ''),
                    'notes': tc_act.display_text or '',
                    'recording_url': '',
                    'details': {
                        'sender_type': 'whatsapp',
                        'status': tc_act.display_status or 'sent'
                    }
                })
            elif 'NOTE' in act_type:
                timeline.append({
                    'timestamp': t.isoformat() if t else '',
                    'display_time': t.strftime('%b %d, %Y %I:%M %p') if t else '',
                    'type': 'note',
                    'icon': 'file-text',
                    'color': '#0284c7' if 'SYSTEM' not in act_type else '#64748b',
                    'bg_color': '#f0f9ff' if 'SYSTEM' not in act_type else '#f8fafc',
                    'title': f"TeleCRM {act_type.replace('_', ' ').title()}",
                    'description': f"By: {tc_act.employee_uid or 'System'}",
                    'notes': tc_act.display_text or '',
                    'recording_url': '',
                    'details': {
                        'activity_type': tc_act.type,
                        'performed_by': tc_act.employee_uid
                    }
                })
            elif 'STATUS' in act_type:
                timeline.append({
                    'timestamp': t.isoformat() if t else '',
                    'display_time': t.strftime('%b %d, %Y %I:%M %p') if t else '',
                    'type': 'status',
                    'icon': 'activity',
                    'color': '#475569',
                    'bg_color': '#f8fafc',
                    'title': f"TeleCRM Status: {tc_act.display_old_status} -> {tc_act.display_new_status}",
                    'description': f"By: {tc_act.employee_uid or 'System'}",
                    'notes': tc_act.display_text or '',
                    'recording_url': '',
                    'details': {
                        'old_status': tc_act.display_old_status,
                        'new_status': tc_act.display_new_status,
                        'changed_by': tc_act.employee_uid
                    }
                })
            elif 'FACEBOOK' in act_type or 'META' in act_type:
                timeline.append({
                    'timestamp': t.isoformat() if t else '',
                    'display_time': t.strftime('%b %d, %Y %I:%M %p') if t else '',
                    'type': 'activity',
                    'icon': 'globe',
                    'color': '#2563eb',
                    'bg_color': '#eff6ff',
                    'title': 'TeleCRM Meta Lead Intake',
                    'description': f"Page: {tc_act.campaign_name or 'N/A'} &bull; Form: {tc_act.form_name or 'N/A'}",
                    'notes': tc_act.display_text or '',
                    'recording_url': '',
                    'details': {
                        'campaign': tc_act.campaign_name,
                        'form': tc_act.form_name
                    }
                })

    # Sort chronological descending
    timeline.sort(key=lambda x: x.get('timestamp') or '', reverse=True)

    counselor_name = (lead.assigned_counselor.get_full_name() or lead.assigned_counselor.username) if lead.assigned_counselor else None
    telecaller_name = (lead.assigned_telecaller.get_full_name() or lead.assigned_telecaller.username) if lead.assigned_telecaller else None

    total_calls_count = lead.calls.count()
    if total_calls_count == 0 and tc_call_count > 0:
        total_calls_count = tc_call_count

    payload = {
        'success': True,
        'student': {
            'id': lead.id,
            'name': lead.name,
            'phone': lead.phone,
            'email': lead.email or '',
            'course': lead.product.name if lead.product else (lead.category or 'Not specified'),
            'branch': lead.branch.name if lead.branch else 'Unassigned',
            'status': lead.status,
            'assigned_counselor': counselor_name,
            'assigned_telecaller': telecaller_name,
            'created_at': lead.created_at.strftime('%b %d, %Y %I:%M %p') if lead.created_at else '',
            'enrollment_number': enrollment_number,
            'enrollment_status': enrollment_status,
        },
        'summary': {
            'total_calls': total_calls_count,
            'total_paid': total_paid,
            'total_payable': total_payable,
            'balance_due': max(0.0, total_payable - total_paid),
            'timeline_events_count': len(timeline),
        },
        'timeline': timeline
    }
    return JsonResponse(payload)
