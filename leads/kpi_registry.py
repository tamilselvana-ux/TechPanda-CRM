"""
iTechPanda CRM — Centralized KPI Master Registry (Single Source of Truth)
Defines uniform definitions, Q-filter mappings, and drilldown URL specifications
across Admin, Branch Head, Sales Head, Counselor, and Telecaller dashboards.
"""
from django.db.models import Q
from leads.models import Lead, LeadStatus
from calls.models import CallHistory
from followups.models import FollowUp, FollowUpStatus
from leads.models_enrollment import Enrollment, EnrollmentStatus

KPI_DEFINITIONS = {
    'admin': {
        'total_leads': {
            'label': 'Total Inbound Leads',
            'target_view': 'admin_leads_list',
            'param': 'view',
            'value': 'all',
            'q_filter': lambda dt_start, dt_end: Q(created_at__range=(dt_start, dt_end)) if dt_start and dt_end else Q(),
        },
        'new_leads': {
            'label': 'New Leads',
            'target_view': 'admin_leads_list',
            'param': 'status',
            'value': 'New',
            'q_filter': lambda dt_start, dt_end: Q(status=LeadStatus.NEW, created_at__range=(dt_start, dt_end)) if dt_start and dt_end else Q(status=LeadStatus.NEW),
        },
        'active_leads': {
            'label': 'Active Pipeline Leads',
            'target_view': 'admin_leads_list',
            'param': 'status',
            'value': 'active',
            'q_filter': lambda dt_start, dt_end: Q(status__in=[
                LeadStatus.ATTEMPTED_CONTACT, LeadStatus.CONTACTED, LeadStatus.COUNSELING_SCHEDULED,
                LeadStatus.COUNSELING, LeadStatus.VISIT_SCHEDULED, LeadStatus.VISITED
            ], created_at__range=(dt_start, dt_end)) if dt_start and dt_end else Q(status__in=[
                LeadStatus.ATTEMPTED_CONTACT, LeadStatus.CONTACTED, LeadStatus.COUNSELING_SCHEDULED,
                LeadStatus.COUNSELING, LeadStatus.VISIT_SCHEDULED, LeadStatus.VISITED
            ]),
        },
        'overdue_followups': {
            'label': 'Overdue Follow-ups',
            'target_view': 'admin_followups_list',
            'param': 'status',
            'value': 'overdue',
            'q_filter': lambda dt_start, dt_end: Q(status=FollowUpStatus.PENDING),
        },
        'total_calls': {
            'label': 'Total Calls Made',
            'target_view': 'admin_calls_list',
            'param': None,
            'value': None,
            'q_filter': lambda dt_start, dt_end: Q(call_start_time__range=(dt_start, dt_end)) if dt_start and dt_end else Q(),
        },
        'completed_calls': {
            'label': 'Completed Calls',
            'target_view': 'admin_calls_list',
            'param': 'status',
            'value': 'Completed',
            'q_filter': lambda dt_start, dt_end: Q(call_status='Completed', call_start_time__range=(dt_start, dt_end)) if dt_start and dt_end else Q(call_status='Completed'),
        },
        'enrolled_students': {
            'label': 'Enrolled Students',
            'target_view': 'admin_enrolled_students',
            'param': None,
            'value': None,
            'q_filter': lambda dt_start, dt_end: Q(status=EnrollmentStatus.ACTIVE),
        },
    },
    'branch_head': {
        'total_leads': {
            'label': 'Total Branch Leads',
            'target_view': 'branch_head_leads_list',
            'param': None,
            'value': None,
        },
        'attended_leads': {
            'label': 'Attended Leads',
            'target_view': 'branch_head_leads_list',
            'param': 'status_group',
            'value': 'attended',
        },
        'visits': {
            'label': 'Center Visits',
            'target_view': 'branch_head_leads_list',
            'param': 'status_group',
            'value': 'visits',
        },
        'enrolled': {
            'label': 'Enrolled Students',
            'target_view': 'admin_enrolled_students',
            'param': None,
            'value': None,
        },
        'rnr': {
            'label': 'RNR Leads',
            'target_view': 'branch_head_leads_list',
            'param': 'status_group',
            'value': 'rnr',
        },
        'pending_followups': {
            'label': 'Pending Follow-ups',
            'target_view': 'admin_followups_list',
            'param': 'status',
            'value': 'pending',
        },
    },
    'counselor': {
        'my_leads': {
            'label': 'My Leads',
            'target_view': 'counselor_leads_list',
            'param': None,
            'value': None,
        },
        'visits': {
            'label': 'Center Visits',
            'target_view': 'counselor_leads_list',
            'param': 'status',
            'value': 'Visited',
        },
        'counseling': {
            'label': 'Counseling in Progress',
            'target_view': 'counselor_leads_list',
            'param': 'status',
            'value': 'Counseling',
        },
        'pending_followups': {
            'label': 'Pending Follow-ups',
            'target_view': 'counselor_followups_list',
            'param': 'status',
            'value': 'Pending',
        },
        'enrolled': {
            'label': 'Enrolled Students',
            'target_view': 'counselor_leads_list',
            'param': 'status',
            'value': 'Enrolled',
        },
    },
    'manager': {
        'team_leads': {
            'label': 'My Team Leads',
            'target_view': 'manager_leads_list',
            'param': None,
            'value': None,
        },
        'telecallers': {
            'label': 'My Telecallers',
            'target_view': 'manager_telecallers_list',
            'param': None,
            'value': None,
        },
        'todays_calls': {
            'label': "Today's Calls",
            'target_view': 'manager_calls_list',
            'param': 'date',
            'value': 'today',
        },
        'completed_calls': {
            'label': 'Completed Calls',
            'target_view': 'manager_calls_list',
            'param': 'status',
            'value': 'Completed',
        },
        'pending_followups': {
            'label': 'Pending Follow-ups',
            'target_view': 'admin_followups_list',
            'param': 'status',
            'value': 'Pending',
        },
        'overdue_followups': {
            'label': 'Overdue Follow-ups',
            'target_view': 'admin_followups_list',
            'param': 'status',
            'value': 'overdue',
        },
    },
    'telecaller': {
        'fresh_today': {
            'label': 'Fresh Leads Today',
            'target_view': 'telecaller_leads_list',
            'param': 'filter',
            'value': 'fresh_today',
        },
        'todays_followups': {
            'label': "Today's Follow-ups",
            'target_view': 'telecaller_followups_list',
            'param': 'status',
            'value': 'today',
        },
        'pending_calls': {
            'label': 'Pending Calls Today',
            'target_view': 'telecaller_calls_list',
            'param': 'status',
            'value': 'pending',
        },
        'untouched_7': {
            'label': 'Not Touched 7 Days',
            'target_view': 'telecaller_leads_list',
            'param': 'filter',
            'value': 'untouched_7',
        },
        'untouched_15': {
            'label': 'Not Touched 15 Days',
            'target_view': 'telecaller_leads_list',
            'param': 'filter',
            'value': 'untouched_15',
        },
        'not_picked': {
            'label': 'Call Not Picked',
            'target_view': 'telecaller_leads_list',
            'param': 'filter',
            'value': 'not_picked',
        },
    }
}
