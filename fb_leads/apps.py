import os
import sys
from django.apps import AppConfig


class FbLeadsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fb_leads"
    verbose_name = "Facebook Leads"

    def ready(self):
        # Self-heal schema column if missing in MySQL
        try:
            from django.db import connection
            if connection.vendor == 'mysql':
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = 'fb_leads_facebookpage' 
                        AND COLUMN_NAME = 'sync_cutoff_date'
                    """)
                    row = cursor.fetchone()
                    if row and row[0] == 0:
                        cursor.execute("ALTER TABLE fb_leads_facebookpage ADD COLUMN sync_cutoff_date DATE NULL")
        except Exception:
            pass

        # Only start scheduler when running runserver or production
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") == "true":
            try:
                from .scheduler import ensure_scheduler_running
                ensure_scheduler_running()
            except Exception:
                pass
