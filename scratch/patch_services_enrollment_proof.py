path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\services_enrollment.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == "if not auto_approve and payment_method in ONLINE_PAYMENT_METHODS:":
        new_lines.append("    require_proof = data.get('require_proof', True) if (isinstance(payment_method_or_data, dict) and 'require_proof' in data) else True\n")
        new_lines.append("    if not auto_approve and payment_method in ONLINE_PAYMENT_METHODS and require_proof:\n")
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Updated services_enrollment.py successfully")
