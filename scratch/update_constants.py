constants_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\constants.py'
with open(constants_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("'email': 'admin@digipanda.com'", "'email': 'admin@digipandaacademy.com'")
text = text.replace("'website': 'www.digipanda.com'", "'website': 'www.digipandaacademy.com'")

with open(constants_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated constants.py with admin@digipandaacademy.com and www.digipandaacademy.com!")
