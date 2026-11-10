path = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\conf.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''def get(key):
    return {**DEFAULTS, **getattr(settings, "CALLS", {})}[key]'''

replacement = '''def get(key, default=None):
    merged = {**DEFAULTS, **getattr(settings, "CALLS", {})}
    if default is not None:
        return merged.get(key, default)
    return merged[key]'''

assert target in content, "target not found"
content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched calls/conf.py get() to support default")
