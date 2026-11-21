from django.core.management.base import BaseCommand
from django.utils import timezone
from chat.models import AutomationFlow, AutomationFlowVersion, UserFlowSession
from chat.automation.templates import get_default_admissions_flow_data


class Command(BaseCommand):
    help = "Updates the published Admissions & Training WhatsApp automation flow with the latest welcome message, choices, and TechPanda details."

    def handle(self, *args, **options):
        self.stdout.write("Updating WhatsApp Automation Flows...")
        new_data = get_default_admissions_flow_data()

        flows = AutomationFlow.objects.all()
        if not flows.exists():
            flow = AutomationFlow.objects.create(
                name="Admissions & Training Flow",
                description="Default TechPanda Software Training & Placement Institute student qualification flow.",
                status=AutomationFlow.STATUS_PUBLISHED,
                trigger_type="first_incoming_message",
                trigger_keywords="hi, hello, course, restart, start",
                flow_data=new_data
            )
            ver = AutomationFlowVersion.objects.create(
                flow=flow,
                version_number=1,
                status=AutomationFlowVersion.STATUS_PUBLISHED,
                flow_data=new_data,
                published_at=timezone.now()
            )
            flow.published_version = ver
            flow.save(update_fields=['published_version'])
            self.stdout.write(self.style.SUCCESS(f"Created and published new AutomationFlow ID: {flow.id} (v1)"))
            return

        updated_count = 0
        for f in flows:
            f.flow_data = new_data
            f.status = AutomationFlow.STATUS_PUBLISHED

            # Update or get/create published AutomationFlowVersion
            ver = f.published_version
            if not ver:
                ver = AutomationFlowVersion.objects.filter(flow=f, version_number=f.version).first()
            if not ver:
                ver = AutomationFlowVersion.objects.create(
                    flow=f,
                    version_number=f.version,
                    status=AutomationFlowVersion.STATUS_PUBLISHED,
                    flow_data=new_data,
                    published_at=timezone.now()
                )
            else:
                ver.flow_data = new_data
                ver.status = AutomationFlowVersion.STATUS_PUBLISHED
                ver.published_at = timezone.now()
                ver.save(update_fields=['flow_data', 'status', 'published_at'])

            f.published_version = ver
            f.save(update_fields=['flow_data', 'status', 'published_version', 'updated_at'])
            updated_count += 1
            self.stdout.write(self.style.SUCCESS(f"Updated and published AutomationFlow ID: {f.id} ('{f.name}')"))

        # Clear any stale active/paused sessions so next user message starts fresh
        cleared_count = UserFlowSession.objects.filter(status__in=['active', 'paused']).update(
            status='completed',
            completed_at=timezone.now()
        )
        self.stdout.write(self.style.SUCCESS(f"Reset {cleared_count} stale session(s) to 'completed'."))
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} flow(s)."))
