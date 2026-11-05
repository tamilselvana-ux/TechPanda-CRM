import os

path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\accountant\verification_list.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """              {% if p.transaction_reference %}
              <div style="font-size: 0.73rem; color: #475569; margin-top: 2px;">Ref: <strong>{{ p.transaction_reference }}</strong></div>
              {% endif %}"""

replacement = """              {% if p.transaction_reference %}
              <div style="font-size: 0.73rem; color: #475569; margin-top: 2px;">Ref: <strong>{{ p.transaction_reference }}</strong></div>
              {% if p.transaction_reference in duplicate_refs %}
              <div style="margin-top: 3px;">
                <span class="badge" style="background: #ef4444; color: #ffffff; font-size: 0.68rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; display: inline-flex; align-items: center; gap: 3px; letter-spacing: 0.02em;" title="Warning: This transaction reference exists on multiple payment records!">
                  ⚠️ DUPLICATE UTR
                </span>
              </div>
              {% endif %}
              {% endif %}"""

if target in content:
    content = content.replace(target, replacement, 1)
    print("Replaced target in verification_list.html")
else:
    print("Warning: target not found in verification_list.html")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Finished patching verification_list.html")
