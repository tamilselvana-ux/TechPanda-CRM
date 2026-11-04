import re

# 1. Update CRM/leads/models.py
leads_model_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\models.py'
with open(leads_model_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Add platform field to Lead model if not present
if "platform = models.CharField" not in text:
    old_source_def = "    source = models.CharField(max_length=50, default='Manual', blank=True, db_index=True)"
    new_source_def = """    source = models.CharField(max_length=50, default='Manual', blank=True, db_index=True)
    PLATFORM_CHOICES = (
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('whatsapp', 'WhatsApp'),
        ('google', 'Google'),
        ('direct', 'Direct / Walk-in'),
        ('other', 'Other'),
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='other',
        blank=True,
        db_index=True,
        help_text="Ad network origin platform (e.g. fb vs ig)"
    )"""
    text = text.replace(old_source_def, new_source_def, 1)

# Add Instagram to CANONICAL_LEAD_SOURCES
old_canonical = """CANONICAL_LEAD_SOURCES = [
    'WhatsApp',
    'Facebook',
    'Website',
    'Google Sheets',
    'Walk-in',
    'Google Call',
    'Manual',
]"""

new_canonical = """CANONICAL_LEAD_SOURCES = [
    'WhatsApp',
    'Facebook',
    'Instagram',
    'Website',
    'Google Sheets',
    'Walk-in',
    'Google Call',
    'Manual',
]"""
text = text.replace(old_canonical, new_canonical, 1)

# Update normalize_lead_source
old_norm_func = """def normalize_lead_source(src: str) -> str:
    \"\"\"Normalizes raw lead source strings into canonical CRM lead sources.\"\"\"
    if not src:
        return ''
    s = str(src).strip()
    sl = s.lower()
    if 'walk' in sl:
        return 'Walk-in'
    if 'whatsapp' in sl:
        return 'WhatsApp'
    if 'facebook' in sl or 'meta' in sl or 'lead form' in sl:
        return 'Facebook'
    if 'sheet' in sl:
        return 'Google Sheets'
    if 'google call' in sl or 'call' in sl:
        return 'Google Call'
    if 'web' in sl or 'google ad' in sl or 'seo' in sl:
        return 'Website'
    if 'manual' in sl:
        return 'Manual'
    return s"""

new_norm_func = """def normalize_lead_source(src: str, platform: str = '') -> str:
    \"\"\"Normalizes raw lead source strings into canonical CRM lead sources.\"\"\"
    if not src and not platform:
        return ''
    p = (platform or '').strip().lower()
    if p in ['ig', 'instagram']:
        return 'Instagram'
    if p in ['fb', 'facebook']:
        return 'Facebook'

    s = str(src or '').strip()
    sl = s.lower()
    if 'instagram' in sl or 'insta' in sl or sl == 'ig':
        return 'Instagram'
    if 'walk' in sl:
        return 'Walk-in'
    if 'whatsapp' in sl:
        return 'WhatsApp'
    if 'facebook' in sl or 'meta' in sl or 'lead form' in sl or 'fb' in sl:
        return 'Facebook'
    if 'sheet' in sl:
        return 'Google Sheets'
    if 'google call' in sl or 'call' in sl:
        return 'Google Call'
    if 'web' in sl or 'google ad' in sl or 'seo' in sl:
        return 'Website'
    if 'manual' in sl:
        return 'Manual'
    return s"""

text = text.replace(old_norm_func, new_norm_func, 1)

with open(leads_model_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Updated leads/models.py successfully')

# 2. Update CRM/fb_leads/models.py
fb_model_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\fb_leads\models.py'
with open(fb_model_path, 'r', encoding='utf-8') as f:
    fb_text = f.read()

if "platform = models.CharField" not in fb_text:
    old_target = "    campaign_name = models.CharField(max_length=255, blank=True)"
    new_target = """    campaign_name = models.CharField(max_length=255, blank=True)
    platform = models.CharField(
        max_length=20,
        blank=True,
        default='',
        db_index=True,
        help_text="Origin platform from Meta API (fb, ig)"
    )"""
    fb_text = fb_text.replace(old_target, new_target, 1)

with open(fb_model_path, 'w', encoding='utf-8') as f:
    f.write(fb_text)
print('Updated fb_leads/models.py successfully')
