# 1. Patch admin.py
path_admin = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\admin.py'
with open(path_admin, 'r', encoding='utf-8') as f:
    admin_content = f.read()

target_admin = '''@admin.register(CallDevice)
class CallDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'google_sim_label', 'app_version', 'last_seen_at', 'last_call_sync_at', 'last_recording_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at',)'''

replacement_admin = '''@admin.register(CallDevice)
class CallDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'google_sim_label', 'app_version', 'sync_cutoff_date',
        'allow_historical_sync', 'last_seen_at', 'last_call_sync_at', 'last_recording_at'
    )
    list_editable = ('sync_cutoff_date', 'allow_historical_sync')
    list_filter = ('allow_historical_sync', 'is_charging')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at',)'''

assert target_admin in admin_content, "target_admin not found"
admin_content = admin_content.replace(target_admin, replacement_admin, 1)

with open(path_admin, 'w', encoding='utf-8') as f:
    f.write(admin_content)
print("Successfully patched calls/admin.py")

# 2. Patch views.py
path_views = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\views.py'
with open(path_views, 'r', encoding='utf-8') as f:
    views_content = f.read()

view_func = '''

@login_required
def api_update_device_sync_settings(request, device_id):
    """
    Allows Admin or Sales Head to configure a CallDevice's sync settings:
    - allow_historical_sync (bool)
    - sync_cutoff_date (YYYY-MM-DD or null)
    """
    if not (request.user.is_admin_user or request.user.is_sales_head_user):
        return JsonResponse({'success': False, 'error': 'Forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    
    from .models import CallDevice
    from django.shortcuts import get_object_or_404
    import json
    device = get_object_or_404(CallDevice, pk=device_id)
    
    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        body = request.POST

    if 'allow_historical_sync' in body:
        val = body.get('allow_historical_sync')
        device.allow_historical_sync = bool(val and str(val).lower() not in ('false', '0', 'off'))

    if 'sync_cutoff_date' in body:
        raw_date = str(body.get('sync_cutoff_date') or '').strip()
        if raw_date:
            from datetime import datetime
            try:
                device.sync_cutoff_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid date format (YYYY-MM-DD required)'}, status=400)
        else:
            device.sync_cutoff_date = None

    device.save(update_fields=['allow_historical_sync', 'sync_cutoff_date'])
    return JsonResponse({
        'success': True,
        'device_id': device.pk,
        'allow_historical_sync': device.allow_historical_sync,
        'sync_cutoff_date': device.sync_cutoff_date.strftime('%Y-%m-%d') if device.sync_cutoff_date else None,
        'message': f"Updated sync settings for {device.user.get_full_name() or device.user.username}'s phone"
    })
'''

views_content += view_func
with open(path_views, 'w', encoding='utf-8') as f:
    f.write(views_content)
print("Successfully patched calls/views.py")

# 3. Patch urls.py
path_urls = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\urls.py'
with open(path_urls, 'r', encoding='utf-8') as f:
    urls_content = f.read()

target_urls = '''    path('calls/api/coaching/quick-cards/', views.api_coaching_quick_cards, name='api_coaching_quick_cards'),
]'''

replacement_urls = '''    path('calls/api/coaching/quick-cards/', views.api_coaching_quick_cards, name='api_coaching_quick_cards'),
    path('calls/device/<int:device_id>/update-sync-settings/', views.api_update_device_sync_settings, name='api_update_device_sync_settings'),
]'''

assert target_urls in urls_content, "target_urls not found"
urls_content = urls_content.replace(target_urls, replacement_urls, 1)

with open(path_urls, 'w', encoding='utf-8') as f:
    f.write(urls_content)
print("Successfully patched calls/urls.py")
