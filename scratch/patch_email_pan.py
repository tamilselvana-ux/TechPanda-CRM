path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\emails\payment_receipt.html"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

old_block = """                      Mobile: {{ invoice_config.mobile }}<br/>
                      GSTIN: {{ invoice_config.gstin }}<br/>
                      Email: {{ invoice_config.email }}<br/>"""

new_block = """                      Mobile: {{ invoice_config.mobile }}<br/>
                      GSTIN: {{ invoice_config.gstin }}<br/>
                      PAN Number: {{ invoice_config.pan }}<br/>
                      Email: {{ invoice_config.email }}<br/>"""

if old_block in text.replace("\r\n", "\n"):
    text = text.replace("\r\n", "\n").replace(old_block, new_block, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Added PAN Number to payment_receipt.html")
else:
    print("old_block not found in payment_receipt.html")
