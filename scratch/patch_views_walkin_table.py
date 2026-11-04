path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\views_walkin.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Replace admin_walkin_forms_list, admin_walkin_form_create, and admin_walkin_form_edit
old_views = """@admin_required
def admin_walkin_forms_list(request):

    \"\"\"

    GET /admin/walkin-forms/

    Dashboard listing all Walk-in Enquiry Forms with branch tags, status, and stats.

    \"\"\"

    forms = WalkinEnquiryForm.objects.all().select_related('branch', 'created_by')

    branches = Branch.objects.filter(status='Active').order_by('name')

    # Total stats

    total_forms = forms.count()

    active_forms = forms.filter(is_active=True).count()

    total_submissions = sum(f.submissions_count for f in forms)

    return render(request, 'admin/walkin_forms_list.html', {

        'forms': forms,

        'branches': branches,

        'total_forms': total_forms,

        'active_forms': active_forms,

        'total_submissions': total_submissions,

    })

@admin_required
def admin_walkin_form_create(request):
    \"\"\"Form creation disabled: Student Enquiry Form is the permanent default.\"\"\"
    from django.contrib import messages
    messages.info(request, "The DigiPanda Student Enquiry Form is the permanent standardized Walk-in form. Template creation is disabled.")
    return redirect('admin_walkin_forms_list')

@admin_required
def admin_walkin_form_edit(request, pk):
    \"\"\"Form structure editor disabled: Student Enquiry Form is the permanent default.\"\"\"
    from django.contrib import messages
    messages.info(request, "The DigiPanda Student Enquiry Form is the permanent standardized Walk-in form. Field customization has been locked.")
    return redirect('admin_walkin_forms_list')"""

new_views = """@admin_required
def admin_walkin_forms_list(request):
    \"\"\"
    GET /admin/walkin-forms/
    Dashboard listing all Walk-in Enquiry Forms with search, filtering, pagination and stats.
    \"\"\"
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
    \"\"\"Creates a new Walk-in Enquiry Form.\"\"\"
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
    \"\"\"Updates an existing Walk-in Enquiry Form.\"\"\"
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

    return redirect('admin_walkin_forms_list')"""

import re
pattern = re.compile(r"@admin_required\s+def admin_walkin_forms_list\(request\):.*?def admin_walkin_form_edit\(request, pk\):.*?return redirect\('admin_walkin_forms_list'\)", re.DOTALL)

if pattern.search(code):
    code = pattern.sub(new_views, code, count=1)
    print("Replaced admin_walkin views with enhanced list, create, and edit logic!")
else:
    print("ERROR: admin_walkin pattern not matched!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print("Finished patching views_walkin.py")
