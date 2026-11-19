from django.contrib import admin
from .models import TeleCRMLead, TeleCRMAction, TeleCRMUser, TeleCRMStatusMap, TeleCRMSyncRun


@admin.register(TeleCRMLead)
class TeleCRMLeadAdmin(admin.ModelAdmin):
    list_display = ('telecrm_id', 'phone', 'crm_lead', 'history_fetched', 'telecrm_created_at', 'last_synced_at')
    search_fields = ('telecrm_id', 'phone', 'crm_lead__name', 'crm_lead__phone')
    list_filter = ('history_fetched', 'last_synced_at', 'telecrm_created_at')
    readonly_fields = ('telecrm_id', 'phone', 'raw', 'crm_lead', 'history_fetched', 'telecrm_created_at', 'telecrm_modified_at', 'last_synced_at')


@admin.register(TeleCRMAction)
class TeleCRMActionAdmin(admin.ModelAdmin):
    list_display = ('telecrm_id', 'type', 'lead', 'occurred_at', 'mapped_ok', 'crm_object_type', 'crm_object_id')
    search_fields = ('telecrm_id', 'lead__telecrm_id', 'lead__phone', 'employee_uid', 'crm_object_id')
    list_filter = ('type', 'mapped_ok', 'occurred_at')
    readonly_fields = ('telecrm_id', 'lead', 'type', 'occurred_at', 'employee_uid', 'raw', 'crm_object_type', 'crm_object_id', 'mapped_ok', 'error')


@admin.register(TeleCRMUser)
class TeleCRMUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'uid', 'crm_user')
    search_fields = ('name', 'email', 'uid', 'crm_user__username', 'crm_user__email')
    list_filter = ('crm_user__role',)


@admin.register(TeleCRMStatusMap)
class TeleCRMStatusMapAdmin(admin.ModelAdmin):
    list_display = ('telecrm_status_name', 'telecrm_status_id', 'crm_status', 'notes')
    search_fields = ('telecrm_status_name', 'telecrm_status_id', 'crm_status')
    list_filter = ('crm_status',)
    list_editable = ('crm_status',)


@admin.register(TeleCRMSyncRun)
class TeleCRMSyncRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'kind', 'status', 'started_at', 'finished_at', 'leads_seen', 'leads_created', 'leads_merged', 'actions_created')
    list_filter = ('kind', 'status', 'started_at')
    readonly_fields = ('kind', 'started_at', 'finished_at', 'cursor', 'leads_seen', 'leads_created', 'leads_merged', 'actions_created', 'errors', 'status')
