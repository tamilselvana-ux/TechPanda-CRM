import re

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\views.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update admin_pipeline_statuses_list
old_list_render = """    statuses = list(statuses_qs.order_by('sort_order', 'name'))



    return render(request, 'admin/pipeline_statuses_list.html', {

        'statuses': statuses,

        'search_query': search_query,

        'status_filter': status_filter,

    })"""

new_list_render = """    statuses = list(statuses_qs.order_by('sort_order', 'name'))

    # Calculate live leads count for each status
    from .models import Lead
    lead_counts = Lead.objects.values('status').annotate(total=Count('id'))
    counts_map = {item['status']: item['total'] for item in lead_counts if item['status']}
    for st in statuses:
        st.leads_count = counts_map.get(st.name, 0)

    all_statuses = list(PipelineStatus.objects.all().order_by('sort_order', 'name'))

    return render(request, 'admin/pipeline_statuses_list.html', {
        'statuses': statuses,
        'all_statuses': all_statuses,
        'search_query': search_query,
        'status_filter': status_filter,
    })"""

if old_list_render in code:
    code = code.replace(old_list_render, new_list_render, 1)
    print("Updated admin_pipeline_statuses_list with leads_count and all_statuses!")
else:
    # regex fallback
    pattern = re.compile(r"statuses = list\(statuses_qs\.order_by\('sort_order', 'name'\)\)\s+return render\(request, 'admin/pipeline_statuses_list\.html', \{\s+'statuses': statuses,\s+'search_query': search_query,\s+'status_filter': status_filter,\s+\}\)")
    if pattern.search(code):
        code = pattern.sub(new_list_render, code, count=1)
        print("Updated admin_pipeline_statuses_list via regex!")
    else:
        print("ERROR: old_list_render not found!")

# 2. Update admin_pipeline_status_delete
old_delete = """@admin_required

def admin_pipeline_status_delete(request, pk):

    from .models import PipelineStatus, Lead

    status_obj = get_object_or_404(PipelineStatus, pk=pk)

    if status_obj.is_system_default:
        messages.error(request, "Default system pipeline statuses cannot be deleted. You can mark them Inactive instead.")
        return redirect('admin_pipeline_statuses')

    # CR-7: Block delete if any lead is currently in that status
    leads_count = Lead.objects.filter(status=status_obj.name).count()
    if leads_count > 0:
        messages.error(request, f"Cannot delete: {leads_count} leads have this status. Reassign them first.")
        return redirect('admin_pipeline_statuses')

    name = status_obj.name

    status_obj.delete()

    log_activity(

        user=request.user,

        action="Pipeline Status Deleted",

        description=f"Deleted custom pipeline status '{name}'.",

        object_type="PipelineStatus",

        request=request

    )

    messages.success(request, f"Status '{name}' deleted successfully.")

    return redirect('admin_pipeline_statuses')"""

new_delete = """@admin_required
def admin_pipeline_status_delete(request, pk):
    from .models import PipelineStatus, Lead
    from django.db import transaction

    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('admin_pipeline_statuses')

    status_obj = get_object_or_404(PipelineStatus, pk=pk)
    name = status_obj.name
    leads_count = Lead.objects.filter(status=name).count()
    reassign_to = request.POST.get('reassign_to_status', '').strip()

    if leads_count > 0:
        if not reassign_to:
            messages.error(
                request,
                f"Cannot delete status '{name}': {leads_count} lead{'s' if leads_count > 1 else ''} currently have this status. Please select a status to reassign them to."
            )
            return redirect('admin_pipeline_statuses')

        target_status = PipelineStatus.objects.filter(name=reassign_to).exclude(pk=status_obj.pk).first()
        if not target_status:
            messages.error(request, f"Target reassignment status '{reassign_to}' does not exist.")
            return redirect('admin_pipeline_statuses')

        with transaction.atomic():
            Lead.objects.filter(status=name).update(status=target_status.name)
            status_obj.delete()
            for idx, s in enumerate(PipelineStatus.objects.order_by('sort_order', 'id')):
                if s.sort_order != idx + 1:
                    s.sort_order = idx + 1
                    s.save(update_fields=['sort_order'])

            log_activity(
                user=request.user,
                action="Pipeline Status Deleted & Reassigned",
                description=f"Deleted pipeline status '{name}' and migrated {leads_count} lead(s) to '{target_status.name}'.",
                object_type="PipelineStatus",
                request=request
            )

        messages.success(request, f"Status '{name}' deleted successfully. Migrated {leads_count} lead{'s' if leads_count > 1 else ''} to '{target_status.name}'.")
        return redirect('admin_pipeline_statuses')

    # Safe direct deletion when 0 leads are in status
    with transaction.atomic():
        status_obj.delete()
        for idx, s in enumerate(PipelineStatus.objects.order_by('sort_order', 'id')):
            if s.sort_order != idx + 1:
                s.sort_order = idx + 1
                s.save(update_fields=['sort_order'])

        log_activity(
            user=request.user,
            action="Pipeline Status Deleted",
            description=f"Deleted pipeline status '{name}'.",
            object_type="PipelineStatus",
            request=request
        )

    messages.success(request, f"Status '{name}' deleted successfully.")
    return redirect('admin_pipeline_statuses')"""

pattern_del = re.compile(r"@admin_required\s+def admin_pipeline_status_delete\(request, pk\):.*?return redirect\('admin_pipeline_statuses'\)", re.DOTALL)
if pattern_del.search(code):
    code = pattern_del.sub(new_delete, code, count=1)
    print("Replaced admin_pipeline_status_delete with safe deletion + lead migration logic!")
else:
    print("ERROR: old_delete pattern not found!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print("Finished patching views.py for Task 7")
