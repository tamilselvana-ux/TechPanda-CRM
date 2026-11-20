from django.urls import path
from . import views

urlpatterns = [
    path('', views.marketing_dashboard, name='marketing_dashboard'),
    path('dashboard/', views.marketing_dashboard, name='marketing_dashboard_alias'),
    path('leads/', views.marketing_leads_list, name='marketing_leads_list'),
    path('leads/<int:pk>/', views.marketing_lead_detail, name='marketing_lead_detail'),
    path('leads/export/', views.marketing_export_leads, name='marketing_export_leads'),
]
