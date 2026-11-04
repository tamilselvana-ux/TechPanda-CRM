path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\views.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

import re

new_delete = """@admin_required
@require_POST
def admin_pipeline_status_delete(request, pk):
    from .models import PipelineStatus, Lead
    from django.db import transaction

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

pattern_del = re.compile(r"@admin_required\s+@require_POST\s+def admin_pipeline_status_delete\(request, pk\):.*?return redirect\('admin_pipeline_statuses'\)", re.DOTALL)
if pattern_del.search(code):
    code = pattern_del.sub(new_delete, code, count=1)
    print("Replaced admin_pipeline_status_delete with safe deletion + lead migration logic!")
else:
    print("ERROR: old_delete pattern not found!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
