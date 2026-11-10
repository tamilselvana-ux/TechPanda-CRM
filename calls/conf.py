"""
Settings for the CRM Call Sync integration (Android app -> CRM).
Override any key in config/settings.py:

CALLS = {
    "PRIVATE_MEDIA_ROOT": BASE_DIR / "private_media",  # app recordings live here, NOT in /media/
    "MAX_RECORDING_MB": 50,
    "CALLBACK_WITHIN_MINUTES": 15,      # missed Google call -> follow-up due this soon
    "MATCH_WINDOW_SECONDS": 600,        # recording <-> call matching tolerance
    "GOOGLE_CALL_SOURCE": "Google Call", # Lead.source for leads created by Google Ads calls
    "APP_LOGIN_ROLES": (
        "SUPERADMIN",
        "ADMIN",
        "SALES_HEAD",
        "BRANCH_HEAD",
        "BRANCH_ADMIN",
        "COUNSELOR",
        "TELECALLER",
        "RECEPTIONIST",
        "ACCOUNTANT",
    ),
    "ON_MISSED_CALL": None,             # optional dotted path: function(call_event)
}
"""
from django.conf import settings

DEFAULTS = {
    "PRIVATE_MEDIA_ROOT": None,  # None -> BASE_DIR / "private_media"
    "MAX_RECORDING_MB": 50,
    "CALLBACK_WITHIN_MINUTES": 15,
    "MATCH_WINDOW_SECONDS": 600,
    "GOOGLE_CALL_SOURCE": "Google Call",
    "APP_LOGIN_ROLES": (
        "SUPERADMIN",
        "ADMIN",
        "SALES_HEAD",
        "BRANCH_HEAD",
        "BRANCH_ADMIN",
        "COUNSELOR",
        "TELECALLER",
        "RECEPTIONIST",
        "ACCOUNTANT",
    ),
    "ON_MISSED_CALL": None,
    "ALLOWED_AUDIO_EXTENSIONS": (
        "mp3", "m4a", "aac", "amr", "awb", "wav", "ogg", "oga", "opus", "3gp", "3gpp", "mp4", "webm", "flac",
    ),
    "CALL_SYNC_MAX_AGE_HOURS": 48,      # rolling auto-sync horizon: 48 hours for call logs
    "RECORDING_MAX_AGE_HOURS": 48,      # rolling auto-sync horizon: 48 hours for recordings
    "CALL_SYNC_MAX_AGE_DAYS": 2,        # backward-compatible days reference (48 hours)
    "RECORDING_MAX_AGE_DAYS": 2,        # backward-compatible days reference (48 hours)
}


def get(key, default=None):
    merged = {**DEFAULTS, **getattr(settings, "CALLS", {})}
    if default is not None:
        return merged.get(key, default)
    return merged[key]
