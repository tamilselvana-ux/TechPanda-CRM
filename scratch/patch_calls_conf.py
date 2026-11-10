path = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\conf.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    "ALLOWED_AUDIO_EXTENSIONS": (
        "mp3", "m4a", "aac", "amr", "awb", "wav", "ogg", "oga", "opus", "3gp", "3gpp", "mp4", "webm", "flac",
    ),'''

replacement = '''    "ALLOWED_AUDIO_EXTENSIONS": (
        "mp3", "m4a", "aac", "amr", "awb", "wav", "ogg", "oga", "opus", "3gp", "3gpp", "mp4", "webm", "flac",
    ),
    "CALL_SYNC_MAX_AGE_DAYS": 30,       # skip phone call logs older than 30 days
    "RECORDING_MAX_AGE_DAYS": 60,       # reject uploaded recordings older than 60 days'''

assert target in content, "target not found"
content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched calls/conf.py")
