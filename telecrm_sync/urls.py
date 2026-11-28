from django.urls import path
from . import views

urlpatterns = [
    path('', views.telecrm_sync_dashboard, name='admin_telecrm_sync_dashboard'),
    path('run/', views.telecrm_run_sync_now, name='admin_telecrm_run_sync_now'),
    path('update-status-map/', views.telecrm_update_status_map, name='admin_telecrm_update_status_map'),
    path('update-user-map/', views.telecrm_update_user_map, name='admin_telecrm_update_user_map'),
    path('conflicts/', views.telecrm_sync_conflicts, name='telecrm_sync_conflicts'),
    path('conflicts/<int:conflict_id>/resolve/', views.telecrm_resolve_conflict, name='telecrm_resolve_conflict'),
]
