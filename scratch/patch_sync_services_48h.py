path = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\sync_services.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update ingest_calls signature and logic
target_ingest = '''def ingest_calls(device, calls):
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
            continue'''

replacement_ingest = '''def ingest_calls(device, calls, manual_override=False):
    """Google Ads number calls from the phone's call log. Returns a summary dict for the app."""
    result = {"created": 0, "duplicates": 0, "new_leads": 0, "skipped_stale": 0, "errors": []}
    on_missed = conf.get("ON_MISSED_CALL")
    on_missed = import_string(on_missed) if on_missed else None
    receiver = device.user
    author = display_name(receiver)
    source = conf.get("GOOGLE_CALL_SOURCE")

    # Check if manual historical override is enabled (via parameter or device setting)
    allow_historical = manual_override or getattr(device, "allow_historical_sync", False)

    if allow_historical:
        # In manual override mode: respect device.sync_cutoff_date if set, otherwise allow all history
        if getattr(device, "sync_cutoff_date", None):
            cutoff = timezone.make_aware(datetime.combine(device.sync_cutoff_date, datetime.min.time()), dt_timezone.utc)
        else:
            cutoff = None
    else:
        # Default rolling auto-sync horizon: last 48 hours (already-synced calls remain safe in CRM DB)
        max_age_hours = conf.get("CALL_SYNC_MAX_AGE_HOURS", 48)
        horizon_cutoff = timezone.now() - timedelta(hours=max_age_hours)
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

        # Historical Cutoff Shield: Skip stale calls older than rolling 48-hour cutoff
        # Prevents dialer history from resurrecting deleted leads or polluting CRM
        if cutoff is not None and data["started_at"] < cutoff:
            result["skipped_stale"] += 1
            continue'''

assert target_ingest in content, "target_ingest not found"
content = content.replace(target_ingest, replacement_ingest, 1)

# 2. Update save_recording signature and logic
target_rec = '''def save_recording(device, upload, data):
    """
    data = the app's form fields: device_file_id, phone_number, direction,
    duration_seconds, call_started_at. Returns (drive.CallRecording, created).
    """
    from drive.models import CallRecording

    if upload is None:
        raise RecordingRejected("audio_file is required")
    ext = os.path.splitext(upload.name)[1].lower().lstrip(".")
    if ext not in conf.get("ALLOWED_AUDIO_EXTENSIONS"):
        raise RecordingRejected(f"unsupported file type: .{ext or '?'}")
    max_mb = conf.get("MAX_RECORDING_MB")
    if upload.size > max_mb * 1024 * 1024:
        raise RecordingRejected(f"file larger than {max_mb} MB")

    device_file_id = str(data.get("device_file_id") or "").strip()[:64]
    if not device_file_id:
        raise RecordingRejected("device_file_id is required")
    existing = CallRecording.objects.filter(device=device, device_file_id=device_file_id).first()
    if existing:
        return existing, False

    raw_number = str(data.get("phone_number") or "").strip()[:30]
    phone = phone10(raw_number)
    direction = str(data.get("direction") or "unknown").lower()
    if direction not in dict(CallRecording.DIRECTION_CHOICES):
        direction = "unknown"
    try:
        duration = max(0, int(float(data.get("duration_seconds") or 0)))
    except (TypeError, ValueError):
        duration = 0
    started_at = _parse_started_at(data.get("call_started_at"))
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
        raise RecordingRejected(f"Call recording timestamp ({started_at.strftime('%Y-%m-%d')}) is older than allowable sync cutoff")'''

replacement_rec = '''def save_recording(device, upload, data, manual_override=False):
    """
    data = the app's form fields: device_file_id, phone_number, direction,
    duration_seconds, call_started_at. Returns (drive.CallRecording, created).
    """
    from drive.models import CallRecording

    if upload is None:
        raise RecordingRejected("audio_file is required")
    ext = os.path.splitext(upload.name)[1].lower().lstrip(".")
    if ext not in conf.get("ALLOWED_AUDIO_EXTENSIONS"):
        raise RecordingRejected(f"unsupported file type: .{ext or '?'}")
    max_mb = conf.get("MAX_RECORDING_MB")
    if upload.size > max_mb * 1024 * 1024:
        raise RecordingRejected(f"file larger than {max_mb} MB")

    device_file_id = str(data.get("device_file_id") or "").strip()[:64]
    if not device_file_id:
        raise RecordingRejected("device_file_id is required")
    existing = CallRecording.objects.filter(device=device, device_file_id=device_file_id).first()
    if existing:
        return existing, False

    raw_number = str(data.get("phone_number") or "").strip()[:30]
    phone = phone10(raw_number)
    direction = str(data.get("direction") or "unknown").lower()
    if direction not in dict(CallRecording.DIRECTION_CHOICES):
        direction = "unknown"
    try:
        duration = max(0, int(float(data.get("duration_seconds") or 0)))
    except (TypeError, ValueError):
        duration = 0
    started_at = _parse_started_at(data.get("call_started_at"))
    user = device.user

    # Historical Cutoff Shield: 48-hour rolling window for auto-sync, or manual override
    allow_historical = manual_override or getattr(device, "allow_historical_sync", False)

    if allow_historical:
        if getattr(device, "sync_cutoff_date", None):
            rec_cutoff = timezone.make_aware(datetime.combine(device.sync_cutoff_date, datetime.min.time()), dt_timezone.utc)
        else:
            rec_cutoff = None
    else:
        max_rec_hours = conf.get("RECORDING_MAX_AGE_HOURS", 48)
        rec_horizon_cutoff = timezone.now() - timedelta(hours=max_rec_hours)
        if getattr(device, "sync_cutoff_date", None):
            device_rec_cutoff = timezone.make_aware(datetime.combine(device.sync_cutoff_date, datetime.min.time()), dt_timezone.utc)
            rec_cutoff = max(rec_horizon_cutoff, device_rec_cutoff)
        else:
            rec_cutoff = rec_horizon_cutoff

    if rec_cutoff is not None and started_at and started_at < rec_cutoff:
        raise RecordingRejected(
            f"Call recording timestamp ({started_at.strftime('%Y-%m-%d %H:%M')}) is older than 48-hour rolling sync window "
            f"(enable manual override to import historical audio)"
        )'''

assert target_rec in content, "target_rec not found"
content = content.replace(target_rec, replacement_rec, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched calls/sync_services.py with 48h rolling window and manual override")
