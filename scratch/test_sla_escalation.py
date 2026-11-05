import os
import sys

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import RequestFactory
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from leads.models import Lead, LeadStatus
from branches.models import Branch
from leads.views import manager_leads_list
from accounts.models import UserRole

User = get_user_model()

print("--- TESTING ITEM 144: SALES HEAD STALE LEAD SLA ESCALATION TIMER ---")

# 1. Setup Branch & Sales Head / Manager
branch, _ = Branch.objects.get_or_create(name="T Nagar Test Center", defaults={"address": "T Nagar", "phone": "044-88887777"})
manager, _ = User.objects.get_or_create(
    username="sales_head_sla_test",
    defaults={"role": UserRole.SALES_HEAD, "first_name": "Vikram", "last_name": "Seth", "branch": branch}
)
manager.role = UserRole.SALES_HEAD
manager.branch = branch
manager.save()

now = timezone.now()

# 2. Create leads with distinct timestamps
# Lead A: Fresh (<30m)
lead_fresh, _ = Lead.objects.get_or_create(
    phone="9999900001",
    defaults={"name": "Fresh Student", "status": "New", "branch": branch, "assigned_sales_head": manager}
)
lead_fresh.status = "New"
lead_fresh.assigned_sales_head = manager
lead_fresh.branch = branch
lead_fresh.save()
Lead.objects.filter(id=lead_fresh.id).update(created_at=now - timedelta(minutes=10))
lead_fresh.refresh_from_db()

# Lead B: Warning (30m - 2h)
lead_warn, _ = Lead.objects.get_or_create(
    phone="9999900002",
    defaults={"name": "Warning Student", "status": "New", "branch": branch, "assigned_sales_head": manager}
)
lead_warn.status = "New"
lead_warn.assigned_sales_head = manager
lead_warn.branch = branch
lead_warn.save()
Lead.objects.filter(id=lead_warn.id).update(created_at=now - timedelta(minutes=45))
lead_warn.refresh_from_db()

# Lead C: Breached (>2h)
lead_breached, _ = Lead.objects.get_or_create(
    phone="9999900003",
    defaults={"name": "Breached Student", "status": "New", "branch": branch, "assigned_sales_head": manager}
)
lead_breached.status = "New"
lead_breached.assigned_sales_head = manager
lead_breached.branch = branch
lead_breached.save()
Lead.objects.filter(id=lead_breached.id).update(created_at=now - timedelta(hours=3, minutes=15))
lead_breached.refresh_from_db()

# Lead D: Contacted
lead_contacted, _ = Lead.objects.get_or_create(
    phone="9999900004",
    defaults={"name": "Contacted Student", "status": "Contacted", "branch": branch, "assigned_sales_head": manager}
)
lead_contacted.status = "Contacted"
lead_contacted.assigned_sales_head = manager
lead_contacted.branch = branch
lead_contacted.save()
Lead.objects.filter(id=lead_contacted.id).update(created_at=now - timedelta(hours=5))
lead_contacted.refresh_from_db()

# 3. Test SLA property calculations
assert lead_fresh.sla_info['level'] == 'fresh', f"Expected fresh, got {lead_fresh.sla_info['level']}"
assert lead_fresh.sla_info['is_breached'] is False

assert lead_warn.sla_info['level'] == 'warning', f"Expected warning, got {lead_warn.sla_info['level']}"
assert lead_warn.sla_info['is_breached'] is False

assert lead_breached.sla_info['level'] == 'breached', f"Expected breached, got {lead_breached.sla_info['level']}"
assert lead_breached.sla_info['is_breached'] is True
assert "SLA Breached" in lead_breached.sla_info['text']

assert lead_contacted.sla_info['level'] == 'contacted'
assert lead_contacted.sla_info['is_breached'] is False
print("✅ Test 1 Passed: Lead.sla_info property correctly categorizes Fresh, Warning, Breached, and Contacted states.")

# 4. Test manager_leads_list view SLA filtering
factory = RequestFactory()

# Filter breached only
req_breached = factory.get('/manager/leads/?sla=breached')
req_breached.user = manager
res_breached = manager_leads_list(req_breached)
assert res_breached.status_code == 200
html_breached = res_breached.content.decode('utf-8')
assert "Breached Student" in html_breached
assert "Fresh Student" not in html_breached
print("✅ Test 2 Passed: ?sla=breached query correctly filters leads to only breached records.")

# Test full template rendering
req_all = factory.get('/manager/leads/')
req_all.user = manager
res_all = manager_leads_list(req_all)
assert res_all.status_code == 200
html_all = res_all.content.decode('utf-8')
assert "SLA Status:" in html_all, "Manager view must render SLA Status quick filter pill strip"
assert "Response SLA" in html_all, "Manager view table must render Response SLA column header"
assert "SLA Breached" in html_all, "Manager view table must render SLA Breached badge"
print("✅ Test 3 Passed: Manager Leads Table renders SLA pill strip and Response SLA badges with HTTP 200 OK.")

print("--- ALL TESTS PASSED FOR ITEM 144 ---")
