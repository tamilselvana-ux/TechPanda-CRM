from django.db import migrations
from django.utils import timezone


def sync_techpanda_flow(apps, schema_editor):
    AutomationFlow = apps.get_model('chat', 'AutomationFlow')
    AutomationFlowVersion = apps.get_model('chat', 'AutomationFlowVersion')
    UserFlowSession = apps.get_model('chat', 'UserFlowSession')

    from chat.automation.templates import get_default_admissions_flow_data
    flow_data = get_default_admissions_flow_data()

    # Find existing or create TechPanda default flow
    flow = AutomationFlow.objects.filter(name__icontains="Admissions").first()
    if not flow:
        flow = AutomationFlow.objects.filter(is_active=True).first()

    if not flow:
        flow = AutomationFlow.objects.create(
            name="TechPanda Admissions Flow",
            slug="techpanda-admissions-flow",
            version=1,
            status="published",
            trigger_type="first_incoming_message",
            trigger_keywords="hi, hello, hey, start, menu, info, admission, course, training",
            flow_data=flow_data,
            is_active=True,
            published_at=timezone.now()
        )
    else:
        flow.name = "TechPanda Admissions Flow"
        flow.slug = "techpanda-admissions-flow"
        flow.flow_data = flow_data
        flow.is_active = True
        flow.status = "published"
        flow.trigger_type = "first_incoming_message"
        flow.trigger_keywords = "hi, hello, hey, start, menu, info, admission, course, training"
        flow.published_at = timezone.now()

    # Create or update published version
    ver = AutomationFlowVersion.objects.filter(flow=flow, version_number=flow.version or 1).first()
    if not ver:
        ver = AutomationFlowVersion.objects.create(
            flow=flow,
            version_number=flow.version or 1,
            status="published",
            flow_data=flow_data,
            change_summary="TechPanda default automation flow with updated welcome and qualification",
            published_at=timezone.now()
        )
    else:
        ver.flow_data = flow_data
        ver.status = "published"
        ver.published_at = timezone.now()
        ver.save(update_fields=['flow_data', 'status', 'published_at'])

    flow.published_version = ver
    flow.save(update_fields=['name', 'slug', 'flow_data', 'is_active', 'status', 'trigger_type', 'trigger_keywords', 'published_version', 'published_at'])

    # Clear any stale active/paused sessions so all new messages start fresh on the new flow
    UserFlowSession.objects.filter(status__in=['active', 'paused']).update(
        status='completed',
        completed_at=timezone.now()
    )


def reverse_sync(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0009_businessaccount_app_secret_and_more'),
    ]

    operations = [
        migrations.RunPython(sync_techpanda_flow, reverse_sync),
    ]
