from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q
from leads.models_enrollment import Enrollment, Installment, InstallmentStatus, PaymentEmailLog
from services.email_service import send_installment_reminder_email
from chat.models import Conversation, Message
from activities.utils import log_activity
import logging

logger = logging.getLogger(__name__)


def run_dunning_cycle(target_date=None):
    """
    Automated Multi-Stage Overdue Installment Dunning Engine.
    Scans active student installments and executes idempotent reminders:
      - Stage 1 (T-3 Days): Friendly upcoming payment notice (WhatsApp + Email)
      - Stage 2 (T-0 Due Date): Formal payment due today notice (WhatsApp + Email)
      - Stage 3 (T+5 Days): Overdue escalation & administrative suspension warning
    """
    today = target_date or timezone.localdate()
    t_minus_3 = today + timedelta(days=3)
    t_plus_5 = today - timedelta(days=5)

    summary = {
        'target_date': str(today),
        'stage_1_upcoming': 0,
        'stage_2_due': 0,
        'stage_3_overdue': 0,
        'total_dispatched': 0,
        'errors': []
    }

    # Query active pending installments
    active_installments = Installment.objects.filter(
        enrollment__status='Active',
        remaining_balance__gt=Decimal('0.00')
    ).select_related('enrollment', 'enrollment__lead', 'enrollment__product')

    for inst in active_installments:
        enr = inst.enrollment
        lead = enr.lead
        due = inst.due_date

        stage = None
        email_type = None

        if due == t_minus_3:
            stage = 'STAGE_1_UPCOMING'
            email_type = 'UPCOMING_REMINDER'
        elif due == today:
            stage = 'STAGE_2_DUE_TODAY'
            email_type = 'DUE_REMINDER'
        elif due <= t_plus_5:
            stage = 'STAGE_3_OVERDUE_ESCALATION'
            email_type = 'OVERDUE_REMINDER'

        if not stage:
            continue

        # Idempotency check: Don't dispatch twice for same installment on same day
        already_sent = PaymentEmailLog.objects.filter(
            installment=inst,
            email_type=email_type,
            created_at__date=today,
            status='SENT'
        ).exists()

        if already_sent:
            continue

        try:
            # 1. Dispatch Email Reminder
            email_success = False
            try:
                email_success = send_installment_reminder_email(inst)
            except Exception as e:
                logger.warning("Dunning email failed for inst %s: %s", inst.id, e)

            # 2. Dispatch WhatsApp Dunning Message
            p_digits = ''.join(c for c in (enr.student_phone or '') if c.isdigit())
            if p_digits:
                tail = p_digits[-10:]
                conv = Conversation.objects.filter(
                    Q(phone_number__endswith=tail) | Q(phone_number__icontains=tail)
                ).first()

                if conv:
                    course_name = enr.product.name if enr.product else 'Course'
                    due_date_str = due.strftime('%d %b %Y')
                    amt_str = f"₹{inst.remaining_balance:,.2f}"

                    if stage == 'STAGE_1_UPCOMING':
                        wa_text = (
                            f"Hello {enr.student_name}! 🎓 Friendly reminder from iTechPanda Academy: "
                            f"Installment #{inst.installment_number} of {amt_str} for your {course_name} program "
                            f"is due on *{due_date_str}* (in 3 days).\n\n"
                            f"💳 Pay easily via UPI / Netbanking or visit our branch desk."
                        )
                    elif stage == 'STAGE_2_DUE_TODAY':
                        wa_text = (
                            f"Hello {enr.student_name}! ⚠️ Today is the due date for Installment #{inst.installment_number} "
                            f"({amt_str}) for your {course_name} course at iTechPanda Academy.\n\n"
                            f"Kindly clear the dues today to avoid late fee penalties."
                        )
                    else:  # STAGE_3_OVERDUE_ESCALATION
                        wa_text = (
                            f"🚨 *IMPORTANT NOTICE:* Dear {enr.student_name}, your fee payment of {amt_str} "
                            f"for {course_name} was due on {due_date_str} and is now OVERDUE by 5+ days.\n\n"
                            f"Please contact your Counselor ({lead.assigned_counselor or 'Academy Desk'}) immediately "
                            f"to avoid interruption of batch access and certificate issuance."
                        )

                    Message.objects.create(
                        conversation=conv,
                        sender=Message.SENDER_AGENT,
                        message_type=Message.TYPE_TEXT,
                        message_text=wa_text,
                        status='sent',
                        timestamp=timezone.now()
                    )
                    conv.last_message = f"Dunning alert: {stage}"
                    conv.last_message_time = timezone.now()
                    conv.save(update_fields=['last_message', 'last_message_time'])

            # 3. Log to PaymentEmailLog
            PaymentEmailLog.objects.create(
                email_type=email_type,
                enrollment=enr,
                installment=inst,
                recipient_email=enr.student_email or 'student@example.com',
                recipient_name=enr.student_name,
                subject=f"Dunning Alert: Installment #{inst.installment_number} ({stage})",
                body=f"Dispatched automated dunning reminder for ₹{inst.remaining_balance} due {due}",
                status='SENT',
                sent_at=timezone.now()
            )

            # 4. If Stage 3, update installment status to OVERDUE and log activity
            if stage == 'STAGE_3_OVERDUE_ESCALATION':
                inst.status = InstallmentStatus.OVERDUE
                inst.save(update_fields=['status'])
                from activities.models import Activity
                Activity.objects.create(
                    user=lead.assigned_counselor or lead.assigned_sales_head or None,
                    action="Dunning Escalation",
                    description=f"Automated Stage 3 Dunning triggered: Installment #{inst.installment_number} is 5+ days overdue (₹{inst.remaining_balance:,.2f}).",
                    object_type="Lead",
                    object_id=str(lead.id)
                )
                summary['stage_3_overdue'] += 1
            elif stage == 'STAGE_1_UPCOMING':
                summary['stage_1_upcoming'] += 1
            else:
                summary['stage_2_due'] += 1

            summary['total_dispatched'] += 1

        except Exception as exc:
            logger.error("Error processing dunning for installment %s: %s", inst.id, exc)
            summary['errors'].append(str(exc))

    return summary
