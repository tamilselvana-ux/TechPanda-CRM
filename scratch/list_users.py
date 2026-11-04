import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, 'CRM_Integrated_v2/CRM')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print(f"Total users: {User.objects.count()}")
for u in User.objects.all()[:15]:
    role = getattr(u, 'role', getattr(u, 'user_type', 'N/A'))
    print(f"User: {u.username} | Email: {u.email} | Superuser: {u.is_superuser} | Staff: {u.is_staff} | Role: {role}")
