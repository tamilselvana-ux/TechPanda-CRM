"""
AST-based exact function extractor for CRM/leads/views.py.
Extracts:
- leads/views_desk.py
- leads/views_export.py
- leads/views_allocation.py
"""

import ast

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

def get_ast_function_ranges(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        src = f.read()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)

    funcs = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            start = node.lineno
            if node.decorator_list:
                start = min(d.lineno for d in node.decorator_list)
            end = node.end_lineno
            # Convert 1-indexed to 0-indexed slice
            code_block = "".join(lines[start - 1 : end])
            funcs[node.name] = code_block
    return funcs

def run():
    # Read original views.py before we appended re-exports
    with open('CRM/leads/views.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove previous re-export append if present
    marker = "# ==========================================\n# MODULARIZED SUB-PACKAGE RE-EXPORTS"
    if marker in content:
        content = content[:content.find(marker)].rstrip() + "\n"
        with open('CRM/leads/views.py', 'w', encoding='utf-8') as f:
            f.write(content)

    func_map = get_ast_function_ranges('CRM/leads/views.py')
    print(f"Total top-level functions parsed via AST: {len(func_map)}")

    # 1. Desk
    desk_names = [
        'receptionist_dashboard',
        'receptionist_lead_history',
        'receptionist_check_existing_lead',
        'admin_walkin_desk',
        'admin_walkin_create',
        'admin_walkin_assign_counselor',
        'admin_walkin_bulk_assign_counselor',
        'admin_walkin_update_status',
    ]
    desk_code = COMMON_HEADER + "\n\n" + "\n\n".join(func_map[n] for n in desk_names) + "\n"
    with open('CRM/leads/views_desk.py', 'w', encoding='utf-8') as f:
        f.write(desk_code)
    print("Generated CRM/leads/views_desk.py")

    # 2. Export
    export_names = [
        'export_leads_csv',
        'admin_duplicate_leads_export',
        'admin_duplicate_leads_view',
        'admin_duplicate_lead_payload',
        'admin_duplicate_lead_promote',
        'admin_duplicate_leads_keep_single',
    ]
    export_code = COMMON_HEADER + "\n\n" + "\n\n".join(func_map[n] for n in export_names) + "\n"
    with open('CRM/leads/views_export.py', 'w', encoding='utf-8') as f:
        f.write(export_code)
    print("Generated CRM/leads/views_export.py")

    # 3. Allocation
    allocation_names = [
        'admin_lead_queues',
        'api_bulk_assign_leads',
        'api_bulk_assign_preview',
        'api_reassign_lead_to_counselor',
        'api_resolve_lead_selection',
        'api_bulk_action',
        'admin_retry_pending_assignments',
    ]
    allocation_code = COMMON_HEADER + "\n\n" + "\n\n".join(func_map[n] for n in allocation_names) + "\n"
    with open('CRM/leads/views_allocation.py', 'w', encoding='utf-8') as f:
        f.write(allocation_code)
    print("Generated CRM/leads/views_allocation.py")

    # 4. Re-export in views.py
    re_exports = f"""

# ==========================================
# MODULARIZED SUB-PACKAGE RE-EXPORTS (Phase 6 Architecture)
# ==========================================
from .views_desk import (
    {', '.join(desk_names)}
)
from .views_export import (
    {', '.join(export_names)}
)
from .views_allocation import (
    {', '.join(allocation_names)}
)
"""
    with open('CRM/leads/views.py', 'a', encoding='utf-8') as f:
        f.write(re_exports)
    print("Appended clean re-exports to CRM/leads/views.py")

if __name__ == '__main__':
    run()
