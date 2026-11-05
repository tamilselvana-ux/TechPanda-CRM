import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """
        Auto-heal missing schema columns if production deployment hasn't run migrations.
        Ensures is_on_duty column exists on accounts_user table in MySQL.
        """
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                if connection.vendor == 'mysql':
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                          AND TABLE_NAME = 'accounts_user' 
                          AND COLUMN_NAME = 'is_on_duty';
                    """)
                    row = cursor.fetchone()
                    if row and row[0] == 0:
                        cursor.execute("ALTER TABLE `accounts_user` ADD COLUMN `is_on_duty` TINYINT(1) NOT NULL DEFAULT 1;")
                        logger.info("Auto-healed accounts_user.is_on_duty column in MySQL.")
        except Exception as e:
            # Table might not exist yet during initial setup or migrations, safely ignore
            pass
