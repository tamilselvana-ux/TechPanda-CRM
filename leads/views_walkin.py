import io

import base64

import json

import logging

from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect

from django.http import JsonResponse, HttpResponse

from django.views.decorators.csrf import csrf_exempt

from django.views.decorators.http import require_http_methods

from django.utils import timezone

from django.utils.text import slugify

from django.urls import reverse

from django.contrib.auth.decorators import login_required

from django.db import transaction

from django.db.models import F

import qrcode

import qrcode.image.svg

from accounts.models import User, UserRole
from accounts.permissions import admin_required, role_required

from branches.models import Branch

from lead_channels.models import Channel

from products.models import Product

from leads.models import (

    Lead, LeadCategory, LeadStatus, VisitorStatus, LeadOwnerType,

    DuplicateLeadRecord, WalkinEnquiryForm

)

logger = logging.getLogger(__name__)

def normalize_phone_number(phone_raw):

    """Sanitizes phone input to standard 10 digits for Indian numbers."""

    if not phone_raw:

        return ''

    digits = ''.join(c for c in str(phone_raw) if c.isdigit())

    if digits.startswith('91') and len(digits) == 12:

        digits = digits[2:]

    elif digits.startswith('0') and len(digits) == 11:

        digits = digits[1:]

    return digits[-10:] if len(digits) >= 10 else digits

@require_http_methods(["GET", "POST"])

def public_student_enquiry_form(request, branch_id=None, slug=None):

    """

    Public student-facing enquiry form for Walk-in visitors at the reception desk.

    Accessible without authentication via QR code scan on mobile devices.

    Dynamically renders the active WalkinEnquiryForm schema if available.

    """

    selected_branch = None

    if branch_id:

        selected_branch = Branch.objects.filter(id=branch_id, status='Active').first()

    # Query active branches and products for selection if needed

    active_branches = Branch.objects.filter(status='Active').order_by('name')

    active_products = Product.objects.filter(status='Active').order_by('name')

    # Resolve active form configuration

    form_config = None

    if slug:

        form_config = WalkinEnquiryForm.objects.filter(slug=slug, is_active=True).first()

    if not form_config and selected_branch:

        form_config = WalkinEnquiryForm.objects.filter(branch=selected_branch, is_active=True).first()

    if not form_config:

        form_config = WalkinEnquiryForm.objects.filter(is_default=True, is_active=True).first()

    if not form_config:

        form_config = WalkinEnquiryForm.objects.filter(is_active=True).first()

    # Default branch from form if not explicitly given in URL

    if not selected_branch and form_config and form_config.branch:

        selected_branch = form_config.branch

    schema = form_config.form_schema if form_config else None

    branding = dict((schema.get('branding') if (schema and isinstance(schema, dict)) else {}) or {})

    if not branding.get('icon'):

        branding['icon'] = '🐼'

    if not branding.get('brand_name'):

        branding['brand_name'] = 'itechpanda'

    if not branding.get('subtitle'):

        branding['subtitle'] = (form_config.description if form_config else '') or 'Training & Placement Admission Form' 

    # Calculate live token preview for the form
    preview_now = timezone.now()
    preview_branch_code = (selected_branch.name[:3].upper() if selected_branch and selected_branch.name else 'HQ')
    preview_daily_count = 1
    try:
        preview_walkin_channel = Channel.objects.filter(name='Walk-in').first()
        if preview_walkin_channel and selected_branch:
            today_start = preview_now.replace(hour=0, minute=0, second=0, microsecond=0)
            preview_daily_count = Lead.objects.filter(
                branch=selected_branch,
                created_at__gte=today_start,
                channel=preview_walkin_channel
            ).count() + 1
    except Exception:
        pass
    token_preview = f"WI-{preview_branch_code}-{preview_daily_count:03d}"

    if request.method == "GET":
        return render(request, 'public/student_enquiry_form.html', {
            'form_config': form_config,
            'schema': schema,
            'branding': branding,
            'branch': selected_branch,
            'branches': active_branches,
            'products': active_products,
            'token_preview': token_preview,
            'form_data': {},
        })

    # --- Process POST Submission ---
    try:
        custom_payload = {}
        name = (request.POST.get('name') or request.POST.get('full_name') or '').strip()
        phone_raw = (request.POST.get('phone') or request.POST.get('phone_number') or request.POST.get('mobile') or '').strip()
        email = (request.POST.get('email') or '').strip()
        post_branch_id = request.POST.get('branch_id')
        product_id = request.POST.get('product_id')

        # Basic Information Extraction (Training & Placement Student Enquiry Form)
        custom_payload['enquiry_form_no'] = (request.POST.get('enquiry_form_no') or '').strip()
        custom_payload['enquiry_date'] = (request.POST.get('enquiry_date') or '').strip()
        custom_payload['enquiry_time'] = (request.POST.get('enquiry_time') or '').strip()
        custom_payload['gender'] = (request.POST.get('gender') or '').strip()
        custom_payload['dob'] = (request.POST.get('dob') or '').strip()
        custom_payload['age'] = (request.POST.get('age') or '').strip()
        custom_payload['whatsapp_number'] = (request.POST.get('whatsapp_number') or request.POST.get('whatsapp') or '').strip()
        custom_payload['emergency_contact'] = (request.POST.get('emergency_contact') or request.POST.get('emergency_contact_number') or '').strip()
        custom_payload['preferred_contact'] = (request.POST.get('preferred_contact') or '').strip()

        # Location & Mode
        curr_addr = (request.POST.get('current_address') or request.POST.get('home_address') or request.POST.get('address') or '').strip()
        custom_payload['current_address'] = curr_addr
        custom_payload['home_address'] = curr_addr
        custom_payload['location'] = curr_addr
        custom_payload['city'] = (request.POST.get('city') or '').strip()
        custom_payload['state'] = (request.POST.get('state') or '').strip()
        custom_payload['zip_code'] = (request.POST.get('zip_code') or '').strip()
        pref_mode = (request.POST.get('preferred_training_mode') or request.POST.get('join_preference') or '').strip()
        custom_payload['preferred_training_mode'] = pref_mode
        if pref_mode:
            custom_payload['join_preference'] = pref_mode

        # Education Qualifications
        custom_payload['experience_type'] = (request.POST.get('experience_type') or 'Fresher').strip()
        custom_payload['years_of_experience'] = (request.POST.get('years_of_experience') or '').strip()
        if custom_payload['years_of_experience']:
            custom_payload['total_experience'] = custom_payload['years_of_experience']
        ug_qual = (request.POST.get('ug_qualification') or request.POST.get('ug_degree') or '').strip()
        ug_yop = (request.POST.get('ug_passed_out_year') or request.POST.get('ug_year') or '').strip()
        pg_qual = (request.POST.get('pg_qualification') or request.POST.get('pg_degree') or '').strip()
        pg_yop = (request.POST.get('pg_passed_out_year') or request.POST.get('pg_year') or '').strip()
        custom_payload['ug_qualification'] = ug_qual
        custom_payload['ug_degree'] = ug_qual
        custom_payload['ug_passed_out_year'] = ug_yop
        custom_payload['ug_year'] = ug_yop
        custom_payload['pg_qualification'] = pg_qual
        custom_payload['pg_degree'] = pg_qual
        custom_payload['pg_passed_out_year'] = pg_yop
        custom_payload['pg_year'] = pg_yop
        custom_payload['backlogs'] = (request.POST.get('backlogs') or 'No').strip()
        custom_payload['highest_education'] = (request.POST.get('highest_education') or '').strip()
        if custom_payload['highest_education']:
            custom_payload['degree'] = custom_payload['highest_education']
        elif pg_qual:
            custom_payload['degree'] = pg_qual
        elif ug_qual:
            custom_payload['degree'] = ug_qual
        if pg_yop or ug_yop:
            custom_payload['passed_out'] = pg_yop or ug_yop

        # Work Experience Section
        custom_payload['has_work_experience'] = (request.POST.get('has_work_experience') or '').strip()
        custom_payload['company_name'] = (request.POST.get('company_name') or '').strip()
        custom_payload['designation'] = (request.POST.get('designation') or '').strip()
        custom_payload['work_start_date'] = (request.POST.get('work_start_date') or '').strip()
        custom_payload['work_end_date'] = (request.POST.get('work_end_date') or '').strip()
        custom_payload['current_ctc'] = (request.POST.get('current_ctc') or '').strip()
        custom_payload['it_experience'] = (request.POST.get('it_experience') or '').strip()
        custom_payload['absconded'] = (request.POST.get('absconded') or '').strip()
        custom_payload['has_pf_uan'] = (request.POST.get('has_pf_uan') or '').strip()
        custom_payload['expected_ctc'] = (request.POST.get('expected_ctc') or '').strip()
        custom_payload['reason_for_leaving'] = (request.POST.get('reason_for_leaving') or '').strip()

        # Backward-compatible optional keys (for API / legacy callers)
        if request.POST.get('career_objective'):
            custom_payload['career_objective'] = request.POST.get('career_objective').strip()
        career_goals = request.POST.getlist('career_goals')
        if career_goals:
            custom_payload['career_goals'] = career_goals

        # Interested Courses
        interested_courses = [c.strip() for c in request.POST.getlist('interested_course') if c.strip()]
        course_other = (request.POST.get('course_other_text') or '').strip()
        if course_other:
            custom_payload['course_other_text'] = course_other
            if 'Others' in interested_courses:
                interested_courses = [f"Others ({course_other})" if c == 'Others' else c for c in interested_courses]
            else:
                interested_courses.append(f"Others ({course_other})")
        custom_payload['interested_course'] = interested_courses
        course_track = ', '.join(interested_courses) if interested_courses else (request.POST.get('course_track') or '').strip()

        # Student References
        ref1 = (request.POST.get('student_reference_1') or request.POST.get('ref_1_name') or '').strip()
        ref2 = (request.POST.get('student_reference_2') or request.POST.get('ref_2_name') or '').strip()
        custom_payload['student_reference_1'] = ref1
        custom_payload['student_reference_2'] = ref2
        if request.POST.get('ref_1_name'):
            custom_payload['reference_1_name'] = request.POST.get('ref_1_name').strip()
        if request.POST.get('ref_1_phone'):
            custom_payload['reference_1_phone'] = request.POST.get('ref_1_phone').strip()

        # Helper data dict for redisplay on validation error
        form_data_dict = dict(request.POST.items())
        form_data_dict['interested_course_list'] = interested_courses
        form_data_dict['interested_course_str'] = ' | '.join(interested_courses)
        if not name or not phone_raw:

            return render(request, 'public/student_enquiry_form.html', {

                'form_config': form_config,

                'schema': schema,

                'branch': selected_branch,

                'branches': active_branches,

                'products': active_products,

                'error': 'Please enter your Full Name and Mobile Phone Number.',

                'form_data': form_data_dict,
                'token_preview': token_preview,

            }, status=400)

        phone_clean = normalize_phone_number(phone_raw)

        if len(phone_clean) < 10:

            return render(request, 'public/student_enquiry_form.html', {

                'form_config': form_config,

                'schema': schema,

                'branch': selected_branch,

                'branches': active_branches,

                'products': active_products,

                'error': 'Please enter a valid 10-digit mobile phone number.',

                'form_data': form_data_dict,
                'token_preview': token_preview,

            }, status=400)

        # Resolve branch

        branch = selected_branch

        if not branch and post_branch_id:

            branch = Branch.objects.filter(id=post_branch_id).first()

        if not branch and form_config and form_config.branch:

            branch = form_config.branch

        if not branch:

            branch = active_branches.first()

        # Resolve product

        product = None

        if product_id:

            product = Product.objects.filter(id=product_id).first()

        if not product and course_track:
            product = Product.objects.filter(name__icontains=course_track).first()
        if not product and interested_courses:
            for ic in interested_courses:
                p_match = Product.objects.filter(name__icontains=ic).first()
                if p_match:
                    product = p_match
                    break

        custom_payload.update({

            'course_track': course_track,

            'enquiry_submitted_via': 'Walk-in QR Standee',

            'form_name': form_config.title if form_config else 'Default Walk-in Form',

            'submitted_at': timezone.now().isoformat(),

        })

        # Generate sequential token

        now = timezone.now()

        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        walkin_channel, _ = Channel.objects.get_or_create(name='Walk-in', defaults={'status': 'Active'})

        branch_code = (branch.name[:3].upper() if branch and branch.name else 'HQ')

        daily_count = Lead.objects.filter(

            branch=branch,

            created_at__gte=today_start,

            channel=walkin_channel

        ).count() + 1

        token_number = f"WI-{branch_code}-{daily_count:03d}"

        # Route through CentralizedLeadIntakeService for unified duplicate detection,
        # 10-day branch governance, progressive enrichment, and audit logging.
        from leads.intake import CentralizedLeadIntakeService
        summary_parts = [
            f"Student Enquiry Form – Training & Placement submitted.",
            f"Date: {now.strftime('%d-%b-%Y %I:%M %p')} | Token: #{token_number}",
        ]
        if custom_payload.get('enquiry_form_no'):
            summary_parts.append(f"Enquiry Form No: {custom_payload['enquiry_form_no']}")
        if pref_mode:
            summary_parts.append(f"Training Mode: {pref_mode}")
        if custom_payload.get('experience_type'):
            exp_str = custom_payload['experience_type']
            if custom_payload.get('years_of_experience'):
                exp_str += f" ({custom_payload['years_of_experience']} yrs)"
            summary_parts.append(f"Experience: {exp_str}")
        if course_track:
            summary_parts.append(f"Interested Courses: {course_track}")
        if custom_payload.get('has_work_experience') == 'Yes' and custom_payload.get('company_name'):
            summary_parts.append(f"Work Exp: {custom_payload['company_name']} ({custom_payload.get('designation', '')})")
        if ref1 or ref2:
            summary_parts.append(f"Student References: {', '.join(r for r in [ref1, ref2] if r)}")
        initial_notes = "\n".join(summary_parts) + "\n"
        with transaction.atomic():
            intake_res = CentralizedLeadIntakeService.ingest(
                phone=phone_clean,
                source='Walk-in QR Form',
                channel_name='Walk-in',
                name=name,
                email=email,
                branch=branch,
                product=product,
                note=initial_notes,
                token_number=token_number,
                center_visit_date=now,
                visitor_status=VisitorStatus.WAITING,
                data_payload=custom_payload,
                incoming_timestamp=now,
            )
            lead = intake_res.lead
            is_re_enquiry = not intake_res.created

            lead.is_offline = True
            lead.category = LeadCategory.TRAINING
            merged_cf = dict(lead.custom_fields or {})
            merged_cf.update(custom_payload)
            lead.custom_fields = merged_cf
            lead.save(update_fields=['is_offline', 'category', 'custom_fields', 'updated_at'])

            # Increment submission count on form

            if form_config:

                WalkinEnquiryForm.objects.filter(id=form_config.id).update(submissions_count=F('submissions_count') + 1)

        return render(request, 'public/student_enquiry_success.html', {

            'lead': lead,

            'name': name,

            'token_number': token_number,

            'branch': branch,

            'is_re_enquiry': is_re_enquiry,

            'submitted_at': now,

        })

    except Exception as e:

        logger.exception("Failed to process public student enquiry: %s", e)

        return render(request, 'public/student_enquiry_form.html', {

            'form_config': form_config,

            'schema': schema,

            'branch': selected_branch,

            'branches': active_branches,

            'products': active_products,

            'error': f'An unexpected error occurred while submitting your enquiry: {str(e)}',

            'form_data': form_data_dict,
                'token_preview': token_preview,

        }, status=500)

@require_http_methods(["GET", "POST"])

def public_student_enquiry_form_by_slug(request, slug, branch_id=None):

    """Route alias to open a specific walk-in form by its slug."""

    return public_student_enquiry_form(request, branch_id=branch_id, slug=slug)

# ==========================================================================

# Admin Walk-in Forms Dashboard & Visual Studio Views

# ==========================================================================

@admin_required
def admin_walkin_forms_list(request):
    """
    GET /admin/walkin-forms/
    Dashboard listing all Walk-in Enquiry Forms with search, filtering, pagination and stats.
    """
    from django.core.paginator import Paginator
    from django.utils.text import slugify
    from leads.utils_date_filter import extract_normalized_date_range

    forms_qs = WalkinEnquiryForm.objects.all().select_related('branch', 'created_by').order_by('-is_default', '-created_at')
    branches = Branch.objects.filter(status='Active').order_by('name')

    # 1. Search Query
    search_query = request.GET.get('search', '').strip()
    if search_query:
        forms_qs = forms_qs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(slug__icontains=search_query) |
            Q(branch__name__icontains=search_query)
        )

    # 2. Branch Filter
    branch_filter = request.GET.get('branch', '').strip()
    if branch_filter and branch_filter.isdigit():
        forms_qs = forms_qs.filter(branch_id=int(branch_filter))

    # 3. Status Filter
    status_filter = request.GET.get('status', '').strip().lower()
    if status_filter == 'active':
        forms_qs = forms_qs.filter(is_active=True)
    elif status_filter == 'inactive':
        forms_qs = forms_qs.filter(is_active=False)

    # 4. Date Range Filter
    date_info = extract_normalized_date_range(request, default_period='all')
    if date_info['start_dt'] and date_info['end_dt']:
        forms_qs = forms_qs.filter(created_at__range=(date_info['start_dt'], date_info['end_dt']))

    # Statistics (unpaginated counts)
    total_forms = WalkinEnquiryForm.objects.count()
    active_forms = WalkinEnquiryForm.objects.filter(is_active=True).count()
    total_submissions = sum(f.submissions_count for f in WalkinEnquiryForm.objects.all())

    # Pagination
    paginator = Paginator(forms_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/walkin_forms_list.html', {
        'page_obj': page_obj,
        'forms': page_obj.object_list,
        'branches': branches,
        'total_forms': total_forms,
        'active_forms': active_forms,
        'total_submissions': total_submissions,
        'search_query': search_query,
        'selected_branch': branch_filter,
        'status_filter': status_filter,
        'start_date': date_info['start_date'],
        'end_date': date_info['end_date'],
    })

@admin_required
def admin_walkin_form_create(request):
    """Creates a new Walk-in Enquiry Form."""
    from django.utils.text import slugify
    from django.contrib import messages

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        branch_id = request.POST.get('branch', '').strip()
        theme_color = request.POST.get('theme_color', '#4f46e5').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not title:
            messages.error(request, "Form title is required.")
            return redirect('admin_walkin_forms_list')

        # Auto-generate unique slug
        base_slug = slugify(title) or "walkin-form"
        slug = base_slug
        counter = 1
        while WalkinEnquiryForm.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        branch = None
        if branch_id and branch_id.isdigit():
            branch = Branch.objects.filter(id=int(branch_id)).first()

        WalkinEnquiryForm.objects.create(
            title=title,
            slug=slug,
            description=description,
            branch=branch,
            theme_color=theme_color,
            is_active=is_active,
            is_default=False,
            created_by=request.user
        )
        messages.success(request, f"Walk-in form '{title}' created successfully.")
        return redirect('admin_walkin_forms_list')

    return redirect('admin_walkin_forms_list')

@admin_required
def admin_walkin_form_edit(request, pk):
    """Updates an existing Walk-in Enquiry Form."""
    from django.contrib import messages

    form_obj = get_object_or_404(WalkinEnquiryForm, pk=pk)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        branch_id = request.POST.get('branch', '').strip()
        theme_color = request.POST.get('theme_color', '#4f46e5').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not title:
            messages.error(request, "Form title cannot be empty.")
            return redirect('admin_walkin_forms_list')

        branch = None
        if branch_id and branch_id.isdigit():
            branch = Branch.objects.filter(id=int(branch_id)).first()

        form_obj.title = title
        form_obj.description = description
        form_obj.branch = branch
        form_obj.theme_color = theme_color
        form_obj.is_active = is_active
        form_obj.save(update_fields=['title', 'description', 'branch', 'theme_color', 'is_active', 'updated_at'])

        messages.success(request, f"Walk-in form '{title}' updated successfully.")
        return redirect('admin_walkin_forms_list')

    return redirect('admin_walkin_forms_list')

@admin_required
@require_http_methods(["POST"])
def admin_walkin_form_duplicate(request, pk):

    """Duplicates an existing form with a new unique slug."""

    orig = get_object_or_404(WalkinEnquiryForm, pk=pk)

    ts = int(timezone.now().timestamp())

    new_slug = f"{orig.slug}-copy-{ts}"

    new_title = f"{orig.title} (Copy)"

    clone = WalkinEnquiryForm.objects.create(

        title=new_title,

        slug=new_slug,

        description=orig.description,

        branch=orig.branch,

        theme_color=orig.theme_color,

        is_default=False,

        is_active=True,

        form_schema=orig.form_schema,

        created_by=request.user,

    )

    return redirect('admin_walkin_form_edit', pk=clone.pk)

@admin_required
@require_http_methods(["POST"])
def admin_walkin_form_toggle_status(request, pk):

    """Toggles active/inactive status."""

    form_obj = get_object_or_404(WalkinEnquiryForm, pk=pk)

    form_obj.is_active = not form_obj.is_active

    form_obj.save(update_fields=['is_active', 'updated_at'])

    return redirect('admin_walkin_forms_list')

@admin_required
@require_http_methods(["POST"])
def admin_walkin_form_delete(request, pk):

    """Deletes a form safely."""

    form_obj = get_object_or_404(WalkinEnquiryForm, pk=pk)

    title = form_obj.title

    form_obj.delete()

    return redirect('admin_walkin_forms_list')

@role_required(UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.BRANCH_HEAD, UserRole.RECEPTIONIST)
def walkin_form_qr_standee_view(request, pk):

    """

    Renders a printable A4 Standee Poster for a specific WalkinEnquiryForm.

    """

    form_obj = get_object_or_404(WalkinEnquiryForm, pk=pk)

    branch = form_obj.branch

    if not branch:

        branch = Branch.objects.filter(status='Active').first()

    relative_url = reverse('public_student_enquiry_slug', kwargs={'slug': form_obj.slug})

    enquiry_url = request.build_absolute_uri(relative_url)

    qr_b64 = ''

    qr_svg = ''

    try:

        qr = qrcode.QRCode(

            version=1,

            error_correction=qrcode.constants.ERROR_CORRECT_H,

            box_size=10,

            border=2,

        )

        qr.add_data(enquiry_url)

        qr.make(fit=True)

        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")

        buf = io.BytesIO()

        img.save(buf, format='PNG')

        qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        factory = qrcode.image.svg.SvgPathImage

        svg_qr = qrcode.make(enquiry_url, image_factory=factory, box_size=12, border=2)

        svg_buf = io.BytesIO()

        svg_qr.save(svg_buf)

        qr_svg = svg_buf.getvalue().decode('utf-8')

    except Exception as e:

        logger.exception("Failed to generate QR for form %s: %s", form_obj.id, e)

    branding = dict((form_obj.form_schema or {}).get('branding') or {})

    if not branding.get('icon'):

        branding['icon'] = '🐼'

    if not branding.get('brand_name'):

        branding['brand_name'] = 'itechpanda'

    if not branding.get('subtitle'):

        branding['subtitle'] = form_obj.description or 'Training & Placement Admission Form' 

    return render(request, 'admin/walkin_form_qr_poster.html', {

        'form_obj': form_obj,

        'branch': branch,

        'enquiry_url': enquiry_url,

        'qr_b64': qr_b64,

        'qr_svg': qr_svg,

        'branding': branding,

    })

@role_required(UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.BRANCH_HEAD, UserRole.RECEPTIONIST)
def branch_qr_standee_view(request, branch_id):

    """

    Renders a high-resolution, printable A4 / Desk Standee poster for a specific branch.

    The QR code encodes the branch's direct public walk-in enquiry form URL.

    """

    branch = get_object_or_404(Branch, id=branch_id)

    form_obj = WalkinEnquiryForm.objects.filter(branch=branch, is_active=True).first()

    if not form_obj:

        form_obj = WalkinEnquiryForm.objects.filter(is_default=True, is_active=True).first()

    if form_obj:

        relative_url = reverse('public_student_enquiry_slug_branch', kwargs={'slug': form_obj.slug, 'branch_id': branch.id})

    else:

        relative_url = reverse('public_student_enquiry_branch', kwargs={'branch_id': branch.id})

    enquiry_url = request.build_absolute_uri(relative_url)

    qr_b64 = ''

    qr_svg = ''

    try:

        qr = qrcode.QRCode(

            version=1,

            error_correction=qrcode.constants.ERROR_CORRECT_H,

            box_size=10,

            border=2,

        )

        qr.add_data(enquiry_url)

        qr.make(fit=True)

        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")

        buf = io.BytesIO()

        img.save(buf, format='PNG')

        qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        factory = qrcode.image.svg.SvgPathImage

        svg_qr = qrcode.make(enquiry_url, image_factory=factory, box_size=12, border=2)

        svg_buf = io.BytesIO()

        svg_qr.save(svg_buf)

        qr_svg = svg_buf.getvalue().decode('utf-8')

    except Exception as e:

        logger.exception("Failed to generate QR code for branch %s: %s", branch.id, e)

    return render(request, 'admin/branch_qr_poster.html', {

        'branch': branch,

        'enquiry_url': enquiry_url,

        'qr_b64': qr_b64,

        'qr_svg': qr_svg,

    })

@role_required(UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.BRANCH_HEAD, UserRole.RECEPTIONIST)
def receptionist_qr_standee_view(request):

    """

    Convenience endpoint for receptionists to quickly open their branch's QR Standee.

    """

    user = request.user

    branch = getattr(user, 'branch', None)

    if not branch:

        branch = Branch.objects.filter(status='Active').first()

    if not branch:

        return HttpResponse("No active branch configured in the system.", status=404)

    return redirect('branch_qr_standee', branch_id=branch.id)
