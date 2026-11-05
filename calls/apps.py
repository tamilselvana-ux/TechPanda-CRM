import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class CallsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calls'

    def ready(self):
        """
        Auto-heal missing schema columns if production deployment hasn't run migrations.
        Ensures battery_percent and is_charging columns exist on calls_calldevice table in MySQL.
        """
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                if connection.vendor == 'mysql':
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                          AND TABLE_NAME = 'calls_calldevice' 
                          AND COLUMN_NAME = 'battery_percent';
                    """)
                    row = cursor.fetchone()
                    if row and row[0] == 0:
                        cursor.execute("ALTER TABLE `calls_calldevice` ADD COLUMN `battery_percent` INT NULL;")
                        cursor.execute("ALTER TABLE `calls_calldevice` ADD COLUMN `is_charging` TINYINT(1) NOT NULL DEFAULT 0;")
                        logger.info("Auto-healed calls_calldevice telemetry columns in MySQL.")
        except Exception as e:
            pass
