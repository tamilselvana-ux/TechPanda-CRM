import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST

from leads.models_enrollment import PaymentEmailLog
from services.email_service import (
    send_enrollment_confirmation_email,
    send_payment_receipt_email,
    send_installment_reminder_email,
)

logger = logging.getLogger('crm.emails')


@login_required
def admin_email_logs_list(request):
    """
    Renders searchable, filterable audit log of student email dispatches:
    Enrollment confirmations, verified payment receipts, and installment reminders.
    Only accessible by ADMIN, SUPERADMIN, and ACCOUNTANT roles.
    """
    if request.user.role not in ['ADMIN', 'SUPERADMIN', 'ACCOUNTANT'] and not request.user.is_superuser:
        messages.error(request, "Permission denied: Access restricted to Administrators and Accountants.")
        return redirect('dashboard')

    status_filter = request.GET.get('status', '').strip().upper()
    type_filter = request.GET.get('type', '').strip().upper()
    search_query = request.GET.get('search', '').strip()

    logs_qs = PaymentEmailLog.objects.select_related(
        'enrollment', 'enrollment__product', 'payment', 'installment'
    ).order_by('-created_at')

    if status_filter and status_filter != 'ALL':
        logs_qs = logs_qs.filter(status=status_filter)

    if type_filter and type_filter != 'ALL':
        logs_qs = logs_qs.filter(email_type=type_filter)

    if search_query:
        logs_qs = logs_qs.filter(
            Q(recipient_email__icontains=search_query) |
            Q(recipient_name__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(enrollment__enrollment_number__icontains=search_query)
        )

    # Compute overall statistics
    total_logs = PaymentEmailLog.objects.count()
    sent_count = PaymentEmailLog.objects.filter(status='SENT').count()
    failed_count = PaymentEmailLog.objects.filter(status='FAILED').count()
    pending_count = PaymentEmailLog.objects.filter(status='PENDING').count()

    paginator = Paginator(logs_qs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/email_logs_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search_query': search_query,
        'total_logs': total_logs,
        'sent_count': sent_count,
        'failed_count': failed_count,
        'pending_count': pending_count,
        'email_types': PaymentEmailLog.EMAIL_TYPES,
        'status_choices': PaymentEmailLog.STATUS_CHOICES,
    })


@login_required
@require_POST
def admin_email_log_retry(request, log_id):
    """
    Retries dispatch of a previously failed or pending email.
    """
    if request.user.role not in ['ADMIN', 'SUPERADMIN', 'ACCOUNTANT'] and not request.user.is_superuser:
        messages.error(request, "Permission denied.")
        return redirect('admin_email_logs')

    log = get_object_or_404(PaymentEmailLog, id=log_id)

    success = False
    msg = ""

    try:
        if log.email_type == 'ENROLLMENT_CONFIRMATION':
            success, msg = send_enrollment_confirmation_email(log.enrollment, force_retry=True)
        elif log.email_type == 'PAYMENT_CONFIRMATION' and log.payment:
            success, msg = send_payment_receipt_email(log.payment, force_retry=True)
        elif log.email_type in ['UPCOMING_REMINDER', 'DUE_REMINDER', 'OVERDUE_REMINDER'] and log.installment:
            success, msg = send_installment_reminder_email(log.installment, reminder_type=log.email_type, force_retry=True)
        else:
            msg = f"Cannot retry email of type '{log.email_type}' without associated record."

        if success:
            messages.success(request, f"Email to '{log.recipient_email}' resent successfully.")
        else:
            messages.error(request, f"Retry failed: {msg}")
    except Exception as exc:
        logger.exception("Error retrying email log %s: %s", log_id, exc)
        messages.error(request, f"Retry error: {exc}")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'admin_email_logs'
    return redirect(next_url)
