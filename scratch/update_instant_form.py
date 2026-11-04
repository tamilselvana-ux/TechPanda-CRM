leads_model_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\models.py'
with open(leads_model_path, 'r', encoding='utf-8') as f:
    text = f.read()

target = "if 'facebook' in sl or 'meta' in sl or 'lead form' in sl or 'fb' in sl:"
replacement = "if 'facebook' in sl or 'meta' in sl or 'lead form' in sl or 'instant form' in sl or 'fb' in sl:"

assert target in text, f"Target '{target}' not found in file"
text = text.replace(target, replacement, 1)

with open(leads_model_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Updated instant form in normalize_lead_source successfully')
