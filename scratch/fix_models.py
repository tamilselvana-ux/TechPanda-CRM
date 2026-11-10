fpath = r'd:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\fb_leads\models.py'
with open(fpath, 'r', encoding='utf-8') as f:
    text = f.read()

target = """    token_expires_at = models.DateTimeField(null=True, blank=True)
    sync_cutoff_date = models.DateField(
        null=True,
        blank=True,
        help_text="Historical cutoff date. Leads created before this date will never be synced."
    )
    status = models.CharField(max_length=50, default='CONNECTED', db_index=True)"""

replacement = """    token_expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='CONNECTED', db_index=True)"""

text = text.replace('\r\n', '\n')
target = target.replace('\r\n', '\n')
replacement = replacement.replace('\r\n', '\n')

if target in text:
    text = text.replace(target, replacement, 1)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed FacebookAccount in models.py")
else:
    print("Target not found")
