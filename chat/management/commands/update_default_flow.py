import json
from django.core.management.base import BaseCommand
from chat.models import AutomationFlow
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
            self.stdout.write(self.style.SUCCESS(f"Created and published new AutomationFlow ID: {flow.id}"))
            return

        updated_count = 0
        for f in flows:
            f.flow_data = new_data
            f.status = AutomationFlow.STATUS_PUBLISHED
            f.save(update_fields=['flow_data', 'status', 'updated_at'])
            updated_count += 1
            self.stdout.write(self.style.SUCCESS(f"Updated and published AutomationFlow ID: {f.id} ('{f.name}')"))

        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} flow(s)."))
