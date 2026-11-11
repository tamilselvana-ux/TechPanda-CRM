import os, sys, re, django
sys.path.insert(0, r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import get_resolver

def walk_urls(urlpatterns, prefix=''):
    rows = []
    for p in urlpatterns:
        if hasattr(p, 'url_patterns'):
            rows.extend(walk_urls(p.url_patterns, prefix + str(p.pattern)))
        else:
            name = getattr(p, 'name', '') or ''
            cb = getattr(p, 'callback', None)
            cb_name = f"{cb.__module__}.{cb.__name__}" if cb and hasattr(cb, '__name__') else str(cb)
            rows.append((prefix + str(p.pattern), name, cb_name))
    return rows

all_urls = walk_urls(get_resolver().url_patterns)
print(f"TOTAL URL PATTERNS: {len(all_urls)}")
for pattern, name, cb in sorted(all_urls):
    if not pattern.startswith('admin/'):
        print(f"  /{pattern:<55} | {name:<38} | {cb}")
