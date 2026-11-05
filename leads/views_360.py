from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from leads.models import Lead
from activities.models import Activity
from leads.models_enrollment import Enrollment, PaymentTransaction
from chat.models import Conversation
from leads.duplicates import normalize_phone
import logging

logger = logging.getLogger(__name__)


@login_required
def lead_360_data(request, lead_id):
    """
    Unified 360° Student Admissions Drawer endpoint.
    Aggregates Student Info, CallHistory, WhatsApp Chats, Payment Transactions,
    Enrollments, and Counselor Notes into a single chronological timeline.
    """
    user = request.user
    lead = get_object_or_404(
        Lead.objects.select_related('branch', 'assigned_counselor', 'assigned_telecaller', 'channel', 'product'),
        pk=lead_id
    )

    # Branch access validation if user is restricted
    if user.is_receptionist_user and lead.branch_id and user.branch_id and lead.branch_id != user.branch_id:
        return JsonResponse({'success': False, 'error': 'Branch access restricted.'}, status=403)

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

    # Sort chronological descending
    timeline.sort(key=lambda x: x.get('timestamp') or '', reverse=True)

    counselor_name = (lead.assigned_counselor.get_full_name() or lead.assigned_counselor.username) if lead.assigned_counselor else None
    telecaller_name = (lead.assigned_telecaller.get_full_name() or lead.assigned_telecaller.username) if lead.assigned_telecaller else None

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
            'total_calls': lead.calls.count(),
            'total_paid': total_paid,
            'total_payable': total_payable,
            'balance_due': max(0.0, total_payable - total_paid),
            'timeline_events_count': len(timeline),
        },
        'timeline': timeline
    }
    return JsonResponse(payload)
