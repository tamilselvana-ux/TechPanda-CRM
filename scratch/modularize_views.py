"""
Script to modularize CRM/leads/views.py into:
- leads/views_desk.py
- leads/views_export.py
- leads/views_allocation.py
while maintaining 100% backward compatibility via re-exports in leads/views.py.
"""

import os
import re

COMMON_HEADER = '''import re
import csv
import io
import json
import logging
import openpyxl
from datetime import datetime, timedelta, time
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from accounts.models import User, UserRole
from accounts.permissions import (
    admin_required, lead_allocation_setup_required, sales_head_required, telecaller_required, branch_head_required, counselor_required,
    can_access_lead, can_view_lead, get_accessible_branch_ids,
)
from .handoff_service import change_lead_status
from branches.models import Branch
from lead_channels.models import Channel
from products.models import Product
from followups.models import FollowUp, FollowUpStatus
from calls.models import CallHistory, CallStatus, CallOutcome
from activities.models import Activity
from activities.utils import log_activity
from branches.utils import get_admin_selected_branch
from .models import (
    Lead, LeadStatus, LeadCategory, VisitorStatus, LeadOwnerType, LeadImportHistory,
    GoogleFormConnection, LeadSetupConfig, TelecallerLeadSetup,
    DuplicateLeadRecord, AssignmentMethod
)
from .forms import (
    AdminLeadForm, ManagerLeadForm, TelecallerLeadForm,
    ManagerLeadCreateForm, TelecallerLeadCreateForm, LeadImportForm
)
from .services import import_leads_file
from .duplicates import (
    find_duplicate_lead,
    handle_incoming_lead_duplicate,
    detect_all_duplicate_groups,
    keep_single_lead_for_group,
    process_incoming_lead_with_10day_rule,
    mask_phone,
    process_spreadsheet_row_duplicate_rules,
)
from .assignment import (
    assign_lead_to_branch_telecaller,
    assign_lead_automatically,
    assign_new_lead,
    apply_branch_lead_distribution,
    retry_pending_assignments
)

logger = logging.getLogger('crm')
'''

def extract_function_block(source: str, func_name: str) -> tuple[str, str]:
    """
    Finds @decorator(s) + def func_name(...) up to next top-level def or end of file.
    Returns (extracted_code, remaining_source_with_stub).
    """
    # Pattern to find decorators followed by def func_name
    pattern = rf'((?:^[ \t]*@[^\n]+\n)*^[ \t]*def {func_name}\b.*?)(?=\n(?:(?:@[^\n]+\n)*def |\Z))'
    match = re.search(pattern, source, re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"Function {func_name} not found in source.")
    extracted = match.group(1)
    return extracted

def run_modularization():
    with open('CRM/leads/views.py', 'r', encoding='utf-8') as f:
        views_src = f.read()

    print(f"Original views.py length: {len(views_src.splitlines())} lines")

    # 1. Desk Functions
    desk_funcs = [
        'receptionist_dashboard',
        'receptionist_lead_history',
        'receptionist_check_existing_lead',
        'admin_walkin_desk',
        'admin_walkin_create',
        'admin_walkin_assign_counselor',
        'admin_walkin_bulk_assign_counselor',
        'admin_walkin_update_status',
    ]
    desk_blocks = []
    for fn in desk_funcs:
        block = extract_function_block(views_src, fn)
        desk_blocks.append(block)
    
    with open('CRM/leads/views_desk.py', 'w', encoding='utf-8') as f:
        f.write(COMMON_HEADER + "\n\n" + "\n\n".join(desk_blocks) + "\n")
    print(f"Created CRM/leads/views_desk.py with {len(desk_funcs)} functions")

    # 2. Export Functions
    export_funcs = [
        'export_leads_csv',
        'admin_duplicate_leads_export',
        'admin_duplicate_leads_view',
        'admin_duplicate_lead_payload',
        'admin_duplicate_lead_promote',
        'admin_duplicate_leads_keep_single',
    ]
    export_blocks = []
    for fn in export_funcs:
        block = extract_function_block(views_src, fn)
        export_blocks.append(block)
    
    with open('CRM/leads/views_export.py', 'w', encoding='utf-8') as f:
        f.write(COMMON_HEADER + "\n\n" + "\n\n".join(export_blocks) + "\n")
    print(f"Created CRM/leads/views_export.py with {len(export_funcs)} functions")

    # 3. Allocation Functions
    allocation_funcs = [
        'admin_lead_queues',
        'api_bulk_assign_leads',
        'api_bulk_assign_preview',
        'api_reassign_lead_to_counselor',
        'api_resolve_lead_selection',
        'api_bulk_action',
        'admin_retry_pending_assignments',
    ]
    allocation_blocks = []
    for fn in allocation_funcs:
        block = extract_function_block(views_src, fn)
        allocation_blocks.append(block)
    
    with open('CRM/leads/views_allocation.py', 'w', encoding='utf-8') as f:
        f.write(COMMON_HEADER + "\n\n" + "\n\n".join(allocation_blocks) + "\n")
    print(f"Created CRM/leads/views_allocation.py with {len(allocation_funcs)} functions")

    # Re-export in views.py
    re_exports = f"""
# ==========================================
# MODULARIZED SUB-PACKAGE RE-EXPORTS (Phase 6 Architecture)
# ==========================================
from .views_desk import (
    {', '.join(desk_funcs)}
)
from .views_export import (
    {', '.join(export_funcs)}
)
from .views_allocation import (
    {', '.join(allocation_funcs)}
)
"""
    # Append re-exports to views.py
    with open('CRM/leads/views.py', 'w', encoding='utf-8') as f:
        f.write(views_src + "\n" + re_exports)

    print("Successfully linked all modularized views into CRM/leads/views.py")

if __name__ == '__main__':
    run_modularization()
