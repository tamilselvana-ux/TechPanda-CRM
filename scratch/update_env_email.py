env_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\.env'
with open(env_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('EMAIL_HOST='):
        new_lines.append('EMAIL_HOST=smtp.hostinger.com\n')
    elif line.startswith('EMAIL_PORT='):
        new_lines.append('EMAIL_PORT=465\n')
    elif line.startswith('EMAIL_USE_TLS='):
        new_lines.append('EMAIL_USE_TLS=False\n')
    elif line.startswith('EMAIL_USE_SSL='):
        new_lines.append('EMAIL_USE_SSL=True\n')
    elif line.startswith('EMAIL_HOST_USER='):
        new_lines.append('EMAIL_HOST_USER=admin@digipandaacademy.com\n')
    elif line.startswith('DEFAULT_FROM_EMAIL='):
        new_lines.append('DEFAULT_FROM_EMAIL=DigiPanda Academy <admin@digipandaacademy.com>\n')
    else:
        new_lines.append(line)

# Ensure EMAIL_USE_SSL is present
has_ssl = any(l.startswith('EMAIL_USE_SSL=') for l in new_lines)
if not has_ssl:
    for idx, l in enumerate(new_lines):
        if l.startswith('EMAIL_USE_TLS='):
            new_lines.insert(idx + 1, 'EMAIL_USE_SSL=True\n')
            break

with open(env_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Updated CRM/.env with Hostinger admin@digipandaacademy.com settings!")
