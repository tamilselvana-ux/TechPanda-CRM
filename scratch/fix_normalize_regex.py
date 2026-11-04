import re

leads_model_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\models.py'
with open(leads_model_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure re is imported
if 'import re' not in text:
    text = 'import re\n' + text

old_norm_func = """def normalize_lead_source(src: str, platform: str = '') -> str:
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
    if 'instagram' in sl or bool(re.search(r'\\b(ig|insta)\\b', sl)):
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

text = text.replace(old_norm_func, new_norm_func)

with open(leads_model_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Updated normalize_lead_source with word boundary regex successfully!')
