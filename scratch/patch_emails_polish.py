import re

enroll_path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\emails\enrollment_confirmation.html"
remind_path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\emails\installment_reminder.html"

# 1. Polish enrollment_confirmation.html
with open(enroll_path, "r", encoding="utf-8") as f:
    enroll_html = f.read()

enroll_norm = enroll_html.replace("\r\n", "\n")

# Replace footer logo
enroll_norm = re.sub(
    r'<span style="font-size: 18px; font-weight: 800; color: #38BDF8;">tech</span><span style="font-size: 18px; font-weight: 800; color: #FFFFFF;">panda</span>',
    '<span style="font-size: 18px; font-weight: 800; color: #38bdf8;">digi</span><span style="font-size: 18px; font-weight: 800; color: #4ade80;">p</span><span style="font-size: 18px; font-weight: 800; color: #FFFFFF;">anda</span>',
    enroll_norm
)

# Replace contacts
enroll_norm = enroll_norm.replace("+91 98765 43210", "+91 98846 78282")
enroll_norm = enroll_norm.replace("+919876543210", "+919884678282")
enroll_norm = enroll_norm.replace("support@digipanda.in", "admin@digipanda.com")
enroll_norm = enroll_norm.replace("https://www.digipanda.in", "https://www.digipanda.com")
enroll_norm = enroll_norm.replace("crm.digipanda.in", "www.digipanda.com")
enroll_norm = enroll_norm.replace("www.digipanda.in", "www.digipanda.com")

with open(enroll_path, "w", encoding="utf-8") as f:
    f.write(enroll_norm)
print("Updated enrollment_confirmation.html successfully!")


# 2. Polish installment_reminder.html
with open(remind_path, "r", encoding="utf-8") as f:
    remind_html = f.read()

remind_norm = remind_html.replace("\r\n", "\n")

# Replace footer logo
remind_norm = re.sub(
    r'<span style="font-size: 18px; font-weight: 800; color: #38BDF8;">tech</span><span style="font-size: 18px; font-weight: 800; color: #FFFFFF;">panda</span>',
    '<span style="font-size: 18px; font-weight: 800; color: #38bdf8;">digi</span><span style="font-size: 18px; font-weight: 800; color: #4ade80;">p</span><span style="font-size: 18px; font-weight: 800; color: #FFFFFF;">anda</span>',
    remind_norm
)

# Replace contacts
remind_norm = remind_norm.replace("+91 98765 43210", "+91 98846 78282")
remind_norm = remind_norm.replace("+919876543210", "+919884678282")
remind_norm = remind_norm.replace("support@digipanda.in", "admin@digipanda.com")
remind_norm = remind_norm.replace("https://www.digipanda.in", "https://www.digipanda.com")
remind_norm = remind_norm.replace("crm.digipanda.in", "www.digipanda.com")
remind_norm = remind_norm.replace("www.digipanda.in", "www.digipanda.com")

# Add direct bank transfer option in installment_reminder.html
old_instructions = """              <!-- 6. Payment Instructions Card -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden; margin-bottom: 20px;">"""

new_instructions = """              <!-- Direct Bank Transfer Details -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 16px; padding: 12px 16px;">
                <tr>
                  <td>
                    <div style="font-size: 11.5px; font-weight: 700; color: #1E293B; text-transform: uppercase; margin-bottom: 6px;">
                      Bank Account Details for Direct NEFT / IMPS / UPI Transfer:
                    </div>
                    <div style="font-size: 12px; color: #475569; line-height: 1.5;">
                      <strong>Beneficiary:</strong> DigiPanda Software Training Private Limited<br/>
                      <strong>Bank:</strong> HDFC Bank, CHENNAI - R A PURAM<br/>
                      <strong>Account Number:</strong> 50200115357040<br/>
                      <strong>IFSC Code:</strong> HDFC0000141
                    </div>
                  </td>
                </tr>
              </table>

              <!-- 6. Payment Instructions Card -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden; margin-bottom: 20px;">"""

if old_instructions in remind_norm:
    remind_norm = remind_norm.replace(old_instructions, new_instructions, 1)
    print("Added bank details to installment_reminder.html")
else:
    print("old_instructions not found in installment_reminder.html")

with open(remind_path, "w", encoding="utf-8") as f:
    f.write(remind_norm)
print("Updated installment_reminder.html successfully!")
