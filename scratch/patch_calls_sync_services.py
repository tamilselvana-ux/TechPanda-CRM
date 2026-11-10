path = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\sync_services.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Target for ingest_calls
target1 = '''def ingest_calls(device, calls):
    """Google Ads number calls from the phone's call log. Returns a summary dict for the app."""
    result = {"created": 0, "duplicates": 0, "new_leads": 0, "errors": []}
    on_missed = conf.get("ON_MISSED_CALL")
    on_missed = import_string(on_missed) if on_missed else None
    receiver = device.user
    author = display_name(receiver)
    source = conf.get("GOOGLE_CALL_SOURCE")

    for i, item in enumerate(calls):
        try:
            data = _parse_call(item)
        except (KeyError, TypeError, ValueError) as e:
            result["errors"].append({"index": i, "error": str(e)})
            continue

        if CallEvent.objects.filter(device=device, raw_number=data["raw_number"],
                                    started_at=data["started_at"]).exists():
            result["duplicates"] += 1
            continue'''

replacement1 = '''def ingest_calls(device, calls):
    """Google Ads number calls from the phone's call log. Returns a summary dict for the app."""
    result = {"created": 0, "duplicates": 0, "new_leads": 0, "skipped_stale": 0, "errors": []}
    on_missed = conf.get("ON_MISSED_CALL")
    on_missed = import_string(on_missed) if on_missed else None
    receiver = device.user
    author = display_name(receiver)
    source = conf.get("GOOGLE_CALL_SOURCE")

    max_age_days = conf.get("CALL_SYNC_MAX_AGE_DAYS", 30)
    horizon_cutoff = timezone.now() - timedelta(days=max_age_days)
    if getattr(device, "sync_cutoff_date", None):
        device_cutoff = timezone.make_aware(datetime.combine(device.sync_cutoff_date, datetime.min.time()), dt_timezone.utc)
        cutoff = max(horizon_cutoff, device_cutoff)
    else:
        cutoff = horizon_cutoff

    for i, item in enumerate(calls):
        try:
            data = _parse_call(item)
        except (KeyError, TypeError, ValueError) as e:
            result["errors"].append({"index": i, "error": str(e)})
            continue

        # Historical Cutoff Shield: Skip stale calls older than cutoff threshold
        # Prevents dialer history from resurrecting deleted leads or polluting CRM
        if data["started_at"] < cutoff:
            result["skipped_stale"] += 1
            continue

        if CallEvent.objects.filter(device=device, raw_number=data["raw_number"],
                                    started_at=data["started_at"]).exists():
            result["duplicates"] += 1
            continue'''

assert target1 in content, "target1 not found"
content = content.replace(target1, replacement1, 1)

# Target for save_recording
target2 = '''    started_at = _parse_started_at(data.get("call_started_at"))
    user = device.user

    # Recordings never create leads: personal calls stay out of the CRM.'''

replacement2 = '''    started_at = _parse_started_at(data.get("call_started_at"))
    user = device.user

    # Historical Cutoff Shield: Reject obsolete audio older than allowable sync horizon
    max_rec_days = conf.get("RECORDING_MAX_AGE_DAYS", 60)
    rec_horizon_cutoff = timezone.now() - timedelta(days=max_rec_days)
    if getattr(device, "sync_cutoff_date", None):
        device_rec_cutoff = timezone.make_aware(datetime.combine(device.sync_cutoff_date, datetime.min.time()), dt_timezone.utc)
        rec_cutoff = max(rec_horizon_cutoff, device_rec_cutoff)
    else:
        rec_cutoff = rec_horizon_cutoff

    if started_at and started_at < rec_cutoff:
        raise RecordingRejected(f"Call recording timestamp ({started_at.strftime('%Y-%m-%d')}) is older than allowable sync cutoff")

    # Recordings never create leads: personal calls stay out of the CRM.'''

assert target2 in content, "target2 not found"
content = content.replace(target2, replacement2, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched calls/sync_services.py")
