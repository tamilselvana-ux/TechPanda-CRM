env_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\.env'
with open(env_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('EMAIL_HOST_PASSWORD='):
        new_lines.append('EMAIL_HOST_PASSWORD=Digi_panda!academy@26\n')
    else:
        new_lines.append(line)

with open(env_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Updated EMAIL_HOST_PASSWORD in CRM/.env successfully!")
