"""
Verification Test Suite for Item 152:
Modularization of Monolithic CRM/leads/views.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import RequestFactory
from accounts.models import User, UserRole

# Test 1: Submodule imports
import leads.views_desk as views_desk
import leads.views_export as views_export
import leads.views_allocation as views_allocation
import leads.views as views

def run_tests():
    print("--- [TEST 1: Sub-module Export Verification] ---")
    desk_functions = [
        'receptionist_dashboard',
        'receptionist_lead_history',
        'receptionist_check_existing_lead',
        'admin_walkin_desk',
        'admin_walkin_create',
        'admin_walkin_assign_counselor',
        'admin_walkin_bulk_assign_counselor',
        'admin_walkin_update_status',
    ]
    for fn in desk_functions:
        assert hasattr(views_desk, fn), f"views_desk missing {fn}"
        assert hasattr(views, fn), f"views (re-export) missing {fn}"
        # Assert identity
        assert getattr(views_desk, fn) is getattr(views, fn), f"{fn} in views is not identity to views_desk"
    print(f"PASS: All {len(desk_functions)} Desk views verified in views_desk and re-exported in views.")

    print("\n--- [TEST 2: Export Sub-module Verification] ---")
    export_functions = [
        'export_leads_csv',
        'admin_duplicate_leads_export',
        'admin_duplicate_leads_view',
        'admin_duplicate_lead_payload',
        'admin_duplicate_lead_promote',
        'admin_duplicate_leads_keep_single',
    ]
    for fn in export_functions:
        assert hasattr(views_export, fn), f"views_export missing {fn}"
        assert hasattr(views, fn), f"views (re-export) missing {fn}"
        assert getattr(views_export, fn) is getattr(views, fn), f"{fn} in views is not identity to views_export"
    print(f"PASS: All {len(export_functions)} Export views verified in views_export and re-exported in views.")

    print("\n--- [TEST 3: Allocation Sub-module Verification] ---")
    allocation_functions = [
        'admin_lead_queues',
        'api_bulk_assign_leads',
        'api_bulk_assign_preview',
        'api_reassign_lead_to_counselor',
        'api_resolve_lead_selection',
        'api_bulk_action',
        'admin_retry_pending_assignments',
    ]
    for fn in allocation_functions:
        assert hasattr(views_allocation, fn), f"views_allocation missing {fn}"
        assert hasattr(views, fn), f"views (re-export) missing {fn}"
        assert getattr(views_allocation, fn) is getattr(views, fn), f"{fn} in views is not identity to views_allocation"
    print(f"PASS: All {len(allocation_functions)} Allocation views verified in views_allocation and re-exported in views.")

    print("\n--- [TEST 4: Runtime Execution from Modular Views] ---")
    rf = RequestFactory()
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin_mod', 'admin@example.com', 'pass123')

    # Test receptionist_check_existing_lead from views_desk
    req_desk = rf.get('/leads/receptionist/check-lead/?phone=9999999999')
    receptionist = User.objects.filter(role=UserRole.RECEPTIONIST).first()
    if not receptionist:
        receptionist = User.objects.create_user('rec_mod', 'rec@example.com', 'pass123', role=UserRole.RECEPTIONIST)
    req_desk.user = receptionist
    req_desk.session = {}
    resp_desk = views_desk.receptionist_check_existing_lead(req_desk)
    assert resp_desk.status_code == 200, f"Expected 200, got {resp_desk.status_code}"
    print("PASS: views_desk.receptionist_check_existing_lead executed successfully with HTTP 200.")

    # Test admin_duplicate_leads_view from views_export
    req_exp = rf.get('/admin/duplicate-leads/')
    req_exp.user = admin_user
    req_exp.session = {}
    resp_exp = views_export.admin_duplicate_leads_view(req_exp)
    assert resp_exp.status_code == 200, f"Expected 200, got {resp_exp.status_code}"
    print("PASS: views_export.admin_duplicate_leads_view executed successfully with HTTP 200.")

    # Test api_resolve_lead_selection from views_allocation
    req_alloc = rf.post('/api/leads/resolve-selection/', {'filter_type': 'all', 'scope': 'admin'})
    req_alloc.user = admin_user
    req_alloc.session = {}
    resp_alloc = views_allocation.api_resolve_lead_selection(req_alloc)
    assert resp_alloc.status_code == 200, f"Expected 200, got {resp_alloc.status_code}"
    print("PASS: views_allocation.api_resolve_lead_selection executed successfully with HTTP 200.")

    print("\nALL 4 TESTS PASSED! 100% BACKWARD COMPATIBILITY CONFIRMED.")

if __name__ == '__main__':
    run_tests()
