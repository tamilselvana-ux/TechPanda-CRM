path = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\conf.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    "CALL_SYNC_MAX_AGE_DAYS": 30,       # skip phone call logs older than 30 days
    "RECORDING_MAX_AGE_DAYS": 60,       # reject uploaded recordings older than 60 days'''

replacement = '''    "CALL_SYNC_MAX_AGE_HOURS": 48,      # rolling auto-sync horizon: 48 hours for call logs
    "RECORDING_MAX_AGE_HOURS": 48,      # rolling auto-sync horizon: 48 hours for recordings
    "CALL_SYNC_MAX_AGE_DAYS": 2,        # backward-compatible days reference (48 hours)
    "RECORDING_MAX_AGE_DAYS": 2,        # backward-compatible days reference (48 hours)'''

assert target in content, "target not found"
content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched calls/conf.py with 48h defaults")
