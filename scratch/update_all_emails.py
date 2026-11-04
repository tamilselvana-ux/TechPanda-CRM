import re

# 1. Update installment_reminder.html
with open('CRM_Integrated_v2/CRM/templates/emails/installment_reminder.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_header = """{% if logo_cid %}
                      <img src="cid:{{ logo_cid }}" width="150" height="45" style="width: 150px; height: auto; max-height: 45px; display: block; border: 0;" alt="DigiPanda" />
                      {% else %}
                      <div style="font-family: 'Montserrat', 'Arial Black', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 26px; font-weight: 900; letter-spacing: -0.5px; line-height: 1.1;">
                        <span style="color: #003a93;">digi</span><span style="color: #1da12b;">p</span><span style="color: #1b1817;">anda</span>
                      </div>
                      {% endif %}"""

new_header = """<a href="https://www.digipandaacademy.com" target="_blank" style="text-decoration: none; display: inline-block;">
                        <div style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 32px; font-weight: 900; letter-spacing: -0.5px; line-height: 1;">
                          <span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span>
                        </div>
                      </a>"""

c = c.replace(old_header, new_header)

c = re.sub(r'DIGIPANDA\s*[\u2013-]\s*Learning Today, Building Tomorrow', 
           r"""<span style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 800; font-size: 12px;"><span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span></span> &ndash; Learning Today, Building Tomorrow""", c)

c = c.replace("DigiPanda Software Training Private Limited", 
              """<span style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 800;"><span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span></span> Software Training Private Limited""")

c = c.replace("Thank you for being a part of DIGIPANDA!", 
              """Thank you for being a part of <span style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 800;"><span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span></span>!""")

c = c.replace("&copy; 2026 DIGIPANDA.", 
              """&copy; 2026 <span style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 800;"><span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span></span>.""")

with open('CRM_Integrated_v2/CRM/templates/emails/installment_reminder.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated installment_reminder.html!")

# 2. Update payment_receipt.html
with open('CRM_Integrated_v2/CRM/templates/emails/payment_receipt.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(old_header, new_header)

c = c.replace("from DigiPanda CRM.", 
              """from <span style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 800;"><span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span></span> CRM.""")

with open('CRM_Integrated_v2/CRM/templates/emails/payment_receipt.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated payment_receipt.html!")

# 3. Update user_welcome.html
with open('CRM_Integrated_v2/CRM/templates/emails/user_welcome.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('<h2 class="brand-title">{{ company_name }} CRM</h2>',
              '<h2 class="brand-title"><span style="font-family: \'Century Gothic\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; font-weight: 900; font-size: 26px;"><span style="color: #3b82f6;">digi</span><span style="color: #22c55e;">p</span><span style="color: #ffffff;">anda</span></span> CRM</h2>')

with open('CRM_Integrated_v2/CRM/templates/emails/user_welcome.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated user_welcome.html!")
