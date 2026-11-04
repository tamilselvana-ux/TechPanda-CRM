import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, 'CRM_Integrated_v2/CRM')
django.setup()

from django.apps import apps
from django.urls import get_resolver
from django.conf import settings

out = []
out.append("# Project Inventory: DigiPanda CRM v1.0\n")
out.append(f"**Django Version:** {django.__version__}")
out.append(f"**Base Dir:** {settings.BASE_DIR}")
out.append(f"**Installed Apps:** {', '.join(settings.INSTALLED_APPS)}\n")

out.append("## 1. Models & Database Tables\n")
for model in apps.get_models():
    app_label = model._meta.app_label
    if app_label in ['leads', 'accounts', 'auth']:
        out.append(f"### {model.__name__} (app: `{app_label}`, table: `{model._meta.db_table}`)")
        fields = []
        for f in model._meta.get_fields():
            f_type = f.get_internal_type() if hasattr(f, 'get_internal_type') else f.__class__.__name__
            fields.append(f"`{f.name}` ({f_type})")
        out.append(f"- Fields: {', '.join(fields)}\n")

out.append("## 2. URL Routes\n")
resolver = get_resolver()
def list_urls(patterns, prefix=''):
    routes = []
    for p in patterns:
        if hasattr(p, 'url_patterns'):
            routes.extend(list_urls(p.url_patterns, prefix + str(p.pattern)))
        else:
            routes.append(f"`/{prefix}{str(p.pattern)}` -> `{getattr(p.callback, '__name__', str(p.callback))}`")
    return routes

routes = list_urls(resolver.url_patterns)
for r in sorted(routes):
    out.append(f"- {r}")

with open('docs/project-docs/_inventory.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print(f"Inventory generated with {len(routes)} routes!")
