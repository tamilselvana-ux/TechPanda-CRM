from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.test import TestCase
from django.utils import timezone
from accounts.models import User, UserRole
from branches.models import Branch
from calls.models import CallHistory, CallStatus, CallOutcome
from leads.models import Lead, LeadStatus
from reports.services.metrics import (
    IST,
    format_duration,
    get_period_bounds,
    calculate_total_stats,
    calculate_team_leaderboard,
    get_call_chart_data,
    filter_call_report_leads,
    scope_call_queryset_by_role,
    scope_lead_queryset_by_role,
)


class MetricsServiceTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name='Guindy Central', status='Active')

        self.admin = User.objects.create_superuser(
            username='admin_metrics',
            email='admin@test.com',
            password='password123',
            role=UserRole.SUPERADMIN
        )

        self.counselor = User.objects.create_user(
            username='sugashini_mgr',
            first_name='Sugashini',
            email='suga@test.com',
            password='password123',
            role=UserRole.COUNSELOR,
            branch=self.branch
        )

        self.telecaller1 = User.objects.create_user(
            username='priya_tc',
            first_name='Priya',
            email='priya@test.com',
            password='password123',
            role=UserRole.TELECALLER,
            counselor=self.counselor,
            branch=self.branch
        )

        self.telecaller2 = User.objects.create_user(
            username='rahul_tc',
            first_name='Rahul',
            email='rahul@test.com',
            password='password123',
            role=UserRole.TELECALLER,
            counselor=self.counselor,
            branch=self.branch
        )

        # Unassigned telecaller (no counselor)
        self.unassigned_tc = User.objects.create_user(
            username='direct_agent',
            first_name='Direct Agent',
            email='direct@test.com',
            password='password123',
            role=UserRole.TELECALLER,
            branch=self.branch
        )

        # Create leads
        self.lead1 = Lead.objects.create(
            name='Kavitha R',
            phone='9840112233',
            status=LeadStatus.CONVERTED,
            assigned_telecaller=self.telecaller1,
            branch=self.branch,
            source='Facebook'
        )
        self.lead2 = Lead.objects.create(
            name='Anand M',
            phone='9840223344',
            status=LeadStatus.CONTACTED,
            assigned_telecaller=self.telecaller2,
            branch=self.branch,
            source='Website'
        )
        self.lead3 = Lead.objects.create(
            name='Vimal K',
            phone='9840334455',
            status=LeadStatus.NEW,
            assigned_telecaller=self.unassigned_tc,
            branch=self.branch,
            source='Google Calls'
        )

        now_ist = timezone.now().astimezone(IST)
        # Call 1 by telecaller1: 900 seconds (15m)
        self.call1 = CallHistory.objects.create(
            lead=self.lead1,
            caller=self.telecaller1,
            duration=900,
            call_status='Completed',
            call_outcome=CallOutcome.CONVERTED,
            call_started_at=now_ist,
            recording_url='https://example.com/rec1.mp3'
        )

        # Call 2 by telecaller2: 4500 seconds (1:15h)
        self.call2 = CallHistory.objects.create(
            lead=self.lead2,
            caller=self.telecaller2,
            duration=4500,
            call_status='Completed',
            call_outcome=CallOutcome.FOLLOW_UP_REQUIRED,
            call_started_at=now_ist
        )

        # Call 3 by unassigned agent: 300 seconds (5m)
        self.call3 = CallHistory.objects.create(
            lead=self.lead3,
            caller=self.unassigned_tc,
            duration=300,
            call_status='Completed',
            call_outcome=CallOutcome.INTERESTED,
            call_started_at=now_ist
        )

    def test_format_duration(self):
        self.assertEqual(format_duration(0), '0s')
        self.assertEqual(format_duration(45), '45s')
        self.assertEqual(format_duration(900), '15m')
        self.assertEqual(format_duration(5400), '1:30h')
        self.assertEqual(format_duration(4500), '1:15h')

    def test_get_period_bounds_day_today(self):
        bounds = get_period_bounds(period_type='day', chip='today')
        self.assertEqual(bounds['period_type'], 'day')
        self.assertEqual(bounds['start_dt'].hour, 0)
        self.assertEqual(bounds['start_dt'].minute, 0)
        self.assertEqual(bounds['end_dt'].hour, 23)
        self.assertEqual(bounds['end_dt'].minute, 59)
        self.assertIn('Today', bounds['display_title'])

    def test_calculate_total_stats(self):
        bounds = get_period_bounds(period_type='day', chip='today')
        stats = calculate_total_stats(self.admin, bounds['start_dt'], bounds['end_dt'])

        # 3 calls total (900 + 4500 + 300 = 5700s = 1:35h)
        self.assertEqual(stats['calls'], 3)
        self.assertEqual(stats['connected_calls'], 3)
        self.assertEqual(stats['duration_seconds'], 5700)
        self.assertEqual(stats['duration_formatted'], '1:35h')
        self.assertGreaterEqual(stats['sales'], 1)

    def test_leaderboard_reconciliation(self):
        bounds = get_period_bounds(period_type='day', chip='today')
        total_stats = calculate_total_stats(self.admin, bounds['start_dt'], bounds['end_dt'])
        teams = calculate_team_leaderboard(self.admin, bounds['start_dt'], bounds['end_dt'])

        # Sum of team calls must strictly equal total calls
        team_calls_sum = sum(t['calls'] for t in teams)
        team_duration_sum = sum(t['duration_seconds'] for t in teams)

        self.assertEqual(team_calls_sum, total_stats['calls'])
        self.assertEqual(team_duration_sum, total_stats['duration_seconds'])

    def test_call_chart_data_hourly_sum(self):
        bounds = get_period_bounds(period_type='day', chip='today')
        chart_data = get_call_chart_data(self.admin, bounds['start_dt'], bounds['end_dt'], period_type='day')
        self.assertEqual(len(chart_data['labels']), 24)
        self.assertEqual(sum(chart_data['values']), 3)

    def test_filter_call_report_leads(self):
        bounds = get_period_bounds(period_type='day', chip='today')
        # Filter with recording=Available
        leads = filter_call_report_leads(
            self.admin, bounds['start_dt'], bounds['end_dt'],
            filters={'recording_is': 'Available'}
        )
        self.assertEqual(leads.count(), 1)
        self.assertEqual(leads.first().name, 'Kavitha R')
