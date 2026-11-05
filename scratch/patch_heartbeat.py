import os

path_views = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\views.py'
with open(path_views, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    return JsonResponse({
        'has_device': True,
        'is_online': is_online,
        'app_version': device.app_version or '',
        'last_seen_seconds_ago': int((now - device.last_seen_at).total_seconds()) if device.last_seen_at else None,"""

replacement = """    return JsonResponse({
        'has_device': True,
        'is_online': is_online,
        'battery_percent': device.battery_percent,
        'is_charging': device.is_charging,
        'app_version': device.app_version or '',
        'last_seen_seconds_ago': int((now - device.last_seen_at).total_seconds()) if device.last_seen_at else None,"""

assert target in content, "Target not found in calls/views.py"
content = content.replace(target, replacement, 1)

target2 = """@login_required
@transaction.atomic
def end_call_record(request, pk):"""

replacement2 = """@login_required
def api_device_heartbeat(request):
    \"\"\"
    Heartbeat ping from CallSync companion app or simulated ping.
    Updates last_seen_at, battery_percent, and is_charging.
    \"\"\"
    import json
    from .models import CallDevice
    device, _ = CallDevice.objects.get_or_create(user=request.user)
    device.last_seen_at = timezone.now()

    try:
        data = json.loads(request.body) if request.body else request.POST
    except Exception:
        data = request.POST

    battery = data.get('battery_percent')
    if battery is not None:
        try:
            device.battery_percent = int(battery)
        except (ValueError, TypeError):
            pass

    charging = data.get('is_charging')
    if charging is not None:
        device.is_charging = str(charging).lower() in ('true', '1', 'yes')

    app_ver = data.get('app_version')
    if app_ver:
        device.app_version = str(app_ver)[:20]

    device.save(update_fields=['last_seen_at', 'battery_percent', 'is_charging', 'app_version'])

    return JsonResponse({
        'success': True,
        'is_online': True,
        'battery_percent': device.battery_percent,
        'is_charging': device.is_charging,
        'timestamp': timezone.now().isoformat()
    })


@login_required
@transaction.atomic
def end_call_record(request, pk):"""

assert target2 in content, "Target2 not found in calls/views.py"
content = content.replace(target2, replacement2, 1)

with open(path_views, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated check_device_status and added api_device_heartbeat in calls/views.py")

# Update calls/urls.py
path_urls = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\urls.py'
with open(path_urls, 'r', encoding='utf-8') as f:
    content_urls = f.read()

target_url = """    path('calls/device-status/', views.check_device_status, name='check_device_status'),"""
replacement_url = """    path('calls/device-status/', views.check_device_status, name='check_device_status'),
    path('calls/device/heartbeat/', views.api_device_heartbeat, name='api_device_heartbeat'),"""

assert target_url in content_urls, "target_url not found in calls/urls.py"
content_urls = content_urls.replace(target_url, replacement_url, 1)

with open(path_urls, 'w', encoding='utf-8') as f:
    f.write(content_urls)

print("Updated calls/urls.py with api_device_heartbeat")
