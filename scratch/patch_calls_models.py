path_models = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\models.py'
with open(path_models, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    battery_percent = models.IntegerField(null=True, blank=True, help_text="Device battery percentage (0-100)")
    is_charging = models.BooleanField(default=False, help_text="True if device is plugged into power")
    created_at = models.DateTimeField(auto_now_add=True)'''

replacement = '''    battery_percent = models.IntegerField(null=True, blank=True, help_text="Device battery percentage (0-100)")
    is_charging = models.BooleanField(default=False, help_text="True if device is plugged into power")
    sync_cutoff_date = models.DateField(null=True, blank=True, help_text="Historical cutoff date for call logs and recordings")
    created_at = models.DateTimeField(auto_now_add=True)'''

assert target in content, "target in models.py not found"
content = content.replace(target, replacement, 1)

with open(path_models, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched calls/models.py")

path_apps = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\calls\apps.py'
with open(path_apps, 'r', encoding='utf-8') as f:
    content_apps = f.read()

target_app = '''                    row = cursor.fetchone()
                    if row and row[0] == 0:
                        cursor.execute("ALTER TABLE `calls_calldevice` ADD COLUMN `battery_percent` INT NULL;")
                        cursor.execute("ALTER TABLE `calls_calldevice` ADD COLUMN `is_charging` TINYINT(1) NOT NULL DEFAULT 0;")
                        logger.info("Auto-healed calls_calldevice telemetry columns in MySQL.")'''

replacement_app = '''                    row = cursor.fetchone()
                    if row and row[0] == 0:
                        cursor.execute("ALTER TABLE `calls_calldevice` ADD COLUMN `battery_percent` INT NULL;")
                        cursor.execute("ALTER TABLE `calls_calldevice` ADD COLUMN `is_charging` TINYINT(1) NOT NULL DEFAULT 0;")
                        logger.info("Auto-healed calls_calldevice telemetry columns in MySQL.")
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                          AND TABLE_NAME = 'calls_calldevice' 
                          AND COLUMN_NAME = 'sync_cutoff_date';
                    """)
                    row_cutoff = cursor.fetchone()
                    if row_cutoff and row_cutoff[0] == 0:
                        cursor.execute("ALTER TABLE `calls_calldevice` ADD COLUMN `sync_cutoff_date` DATE NULL;")
                        logger.info("Auto-healed calls_calldevice sync_cutoff_date column in MySQL.")'''

assert target_app in content_apps, "target in apps.py not found"
content_apps = content_apps.replace(target_app, replacement_app, 1)

with open(path_apps, 'w', encoding='utf-8') as f:
    f.write(content_apps)
print("Successfully patched calls/apps.py")
