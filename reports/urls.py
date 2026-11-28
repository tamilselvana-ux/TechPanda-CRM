from django.urls import path
from . import views
from . import views_telecrm

urlpatterns = [
    # TeleCRM Reports & Leaderboard Native Module
    path('reports/leaderboard/', views_telecrm.leaderboard_view, name='reports_leaderboard'),
    path('reports/calls/', views_telecrm.call_report_view, name='reports_calls'),
    path('reports/calls/api/save/', views_telecrm.save_report_api, name='reports_save_report'),
    path('reports/download/', views_telecrm.report_download_view, name='reports_download'),
    path('reports/download/export/', views_telecrm.report_export_action, name='reports_export_action'),
    path('reports/duplicates/', views_telecrm.duplicate_leads_view, name='reports_duplicates'),
    path('reports/duplicates/merge/', views_telecrm.merge_duplicate_api, name='reports_merge_duplicate'),
    path('reports/duplicates/unmark/', views_telecrm.unmark_duplicate_api, name='reports_unmark_duplicate'),
    path('reports/deleted/', views_telecrm.deleted_leads_view, name='reports_deleted'),
    path('reports/deleted/<int:lead_id>/restore/', views_telecrm.restore_lead_api, name='reports_restore_lead'),
    path('reports/deleted/<int:lead_id>/purge/', views_telecrm.purge_lead_api, name='reports_purge_lead'),
    path('reports/lead/<int:lead_id>/star/', views_telecrm.toggle_lead_star_api, name='reports_toggle_star'),

    # Existing reporting endpoints
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('manager/reports/', views.manager_reports, name='manager_reports'),
    path('reports/api/data/', views.reports_api_data, name='reports_api_data'),
    path('reports/api/sync-sheets/', views.reports_api_sync_sheets, name='reports_api_sync_sheets'),
    path('reports/telecaller-rnr/', views.telecaller_rnr_report, name='telecaller_rnr_report'),
    path('reports/telecaller-rnr/leads/', views.telecaller_rnr_lead_drilldown_view, name='telecaller_rnr_lead_drilldown'),
    path('reports/api/management-charts/', views.management_charts_api, name='management_charts_api'),
    path('admin/api/trigger-sla-escalation/', views.trigger_lead_sla_escalation_api, name='admin_trigger_sla_escalation'),
]
