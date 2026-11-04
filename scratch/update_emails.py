import re

with open('CRM_Integrated_v2/CRM/templates/emails/enrollment_confirmation.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace header brand
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

# Replace preheader
c = re.sub(r'DIGIPANDA\s*[\u2013-]\s*Learning Today, Building Tomorrow', 
           r"""<span style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 800; font-size: 12px;"><span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span></span> &ndash; Learning Today, Building Tomorrow""", c)

# Replace Welcome to DIGIPANDA!
c = c.replace("Welcome to DIGIPANDA!", 
              """Welcome to <span style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 800;"><span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span></span>!""")

# Replace at DIGIPANDA
c = c.replace("at DIGIPANDA.", 
              """at <span style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 800;"><span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span></span>.""")

# Replace welcome to DIGIPANDA!
c = c.replace("welcome to DIGIPANDA!", 
              """welcome to <span style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 800;"><span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span></span>!""")

# Replace copyright DIGIPANDA
c = c.replace("&copy; 2026 DIGIPANDA.", 
              """&copy; 2026 <span style="font-family: 'Century Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 800;"><span style="color: #003a93;">digi</span><span style="color: #1ea12c;">p</span><span style="color: #1c1a19;">anda</span></span>.""")

with open('CRM_Integrated_v2/CRM/templates/emails/enrollment_confirmation.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated enrollment_confirmation.html successfully!")
