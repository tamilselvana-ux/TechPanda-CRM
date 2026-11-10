path = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\api_views.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target1 = '''        device = services.device_for_user(request.user, **_app_meta(request))
        return Response(services.ingest_calls(device, calls))'''

replacement1 = '''        device = services.device_for_user(request.user, **_app_meta(request))
        manual_override = bool(
            request.data.get("manual_override") or 
            request.data.get("sync_all") or 
            request.data.get("allow_historical")
        )
        return Response(services.ingest_calls(device, calls, manual_override=manual_override))'''

assert target1 in content, "target1 not found"
content = content.replace(target1, replacement1, 1)

target2 = '''        device = services.device_for_user(request.user, **_app_meta(request))
        try:
            rec, created = services.save_recording(device, request.FILES.get("audio_file"), request.data)'''

replacement2 = '''        device = services.device_for_user(request.user, **_app_meta(request))
        manual_override = str(
            request.data.get("manual_override") or 
            request.data.get("sync_all") or 
            request.data.get("allow_historical") or ""
        ).strip().lower() in ("true", "1", "yes")
        try:
            rec, created = services.save_recording(
                device, request.FILES.get("audio_file"), request.data, manual_override=manual_override
            )'''

assert target2 in content, "target2 not found"
content = content.replace(target2, replacement2, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched calls/api_views.py")
