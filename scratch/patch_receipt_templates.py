import os

pdf_template_path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\leads\receipt_pdf.html"
web_template_path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\leads\receipt.html"
mail_template_path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\emails\payment_receipt.html"

# 1. Update receipt_pdf.html
with open(pdf_template_path, "r", encoding="utf-8") as f:
    pdf_html = f.read()

pdf_html_norm = pdf_html.replace("\r\n", "\n")

old_pdf_sig = """      <!-- Authorised Signatory Block -->
      <div style="margin-top: 10px; text-align: right;">
        {% if signature_path %}
        <div style="margin-bottom: -32px;">
          <img src="{{ signature_path }}" width="125" height="125" style="width: 125px; height: 125px;" alt="Authorized Signatory" />
        </div>
        {% else %}
        <div style="height: 35px;"></div>
        {% endif %}
        <div style="font-size: 7.2pt; font-weight: bold; color: #2d3748; border-top: 1px solid #718096; padding-top: 3px; display: inline-block; min-width: 150px;">
          {{ signatory_label }}
        </div>
      </div>"""

new_pdf_sig = """      <!-- Authorised Signatory Block -->
      <div style="margin-top: 12px; text-align: right;">
        {% if signature_path %}
        <div style="margin-bottom: -10px;">
          <img src="{{ signature_path }}" width="140" height="35" style="width: 140px; height: 35px;" alt="Authorized Signatory" />
        </div>
        {% else %}
        <div style="height: 35px;"></div>
        {% endif %}
        <div style="font-size: 7.2pt; font-weight: bold; color: #2d3748; border-top: 1px solid #718096; padding-top: 3px; display: inline-block; min-width: 150px;">
          {{ signatory_label }}
        </div>
      </div>"""

if old_pdf_sig in pdf_html_norm:
    pdf_html_norm = pdf_html_norm.replace(old_pdf_sig, new_pdf_sig, 1)
    with open(pdf_template_path, "w", encoding="utf-8") as f:
        f.write(pdf_html_norm)
    print("receipt_pdf.html updated successfully!")
else:
    print("old_pdf_sig NOT found in receipt_pdf.html")

# 2. Update receipt.html
with open(web_template_path, "r", encoding="utf-8") as f:
    web_html = f.read()

web_html_norm = web_html.replace("\r\n", "\n")

old_web_sig = """        <!-- Signatory -->
        <div class="signatory-box">
          {% if signature_path or is_authorized %}
          <div style="margin-bottom: -18px; margin-top: -10px;">
            <img src="{% static 'images/shashi_sign.png' %}" style="height: 85px; width: auto; max-width: 170px; object-fit: contain;" alt="Authorized Signatory" />
          </div>
          {% else %}
          <div style="height: 45px;"></div>
          {% endif %}
          <div class="signatory-label">{{ signatory_label }}</div>
        </div>"""

new_web_sig = """        <!-- Signatory -->
        <div class="signatory-box">
          {% if signature_path or is_authorized %}
          <div style="margin-bottom: -8px; margin-top: 0;">
            <img src="{% static 'images/shashi_sign.png' %}" style="height: 42px; width: auto; max-width: 170px; object-fit: contain; display: inline-block;" alt="Authorized Signatory" />
          </div>
          {% else %}
          <div style="height: 42px;"></div>
          {% endif %}
          <div class="signatory-label">{{ signatory_label }}</div>
        </div>"""

if old_web_sig in web_html_norm:
    web_html_norm = web_html_norm.replace(old_web_sig, new_web_sig, 1)
    with open(web_template_path, "w", encoding="utf-8") as f:
        f.write(web_html_norm)
    print("receipt.html updated successfully!")
else:
    print("old_web_sig NOT found in receipt.html")

# 3. Update payment_receipt.html
with open(mail_template_path, "r", encoding="utf-8") as f:
    mail_html = f.read()

mail_html_norm = mail_html.replace("\r\n", "\n")

old_mail_sig = """                    <!-- Signatory -->
                    <div align="right" style="margin-top: 16px;">
                      {% if is_authorized and signature_data_uri %}
                      <div style="margin-bottom: -15px;">
                        <img src="{{ signature_data_uri }}" width="110" height="110" style="width: 110px; height: 110px; display: inline-block; border: none;" alt="Authorized Signatory" />
                      </div>
                      {% elif is_authorized and signature_url %}
                      <div style="margin-bottom: -15px;">
                        <img src="{{ signature_url }}" width="110" height="110" style="width: 110px; height: 110px; display: inline-block; border: none;" alt="Authorized Signatory" />
                      </div>
                      {% else %}
                      <div style="height: 35px;"></div>
                      {% endif %}
                      <div style="font-size: 10px; font-weight: 700; color: #374151; border-top: 1px solid #6B7280; padding-top: 3px; display: inline-block; min-width: 150px;">
                        {{ signatory_label }}
                      </div>
                    </div>"""

new_mail_sig = """                    <!-- Signatory -->
                    <div align="right" style="margin-top: 18px; text-align: right;">
                      {% if is_authorized and signature_data_uri %}
                      <div style="margin-bottom: -8px;">
                        <img src="{{ signature_data_uri }}" width="150" height="38" style="width: 150px; height: 38px; display: inline-block; border: none; object-fit: contain;" alt="Authorized Signatory" />
                      </div>
                      {% elif is_authorized and signature_url %}
                      <div style="margin-bottom: -8px;">
                        <img src="{{ signature_url }}" width="150" height="38" style="width: 150px; height: 38px; display: inline-block; border: none; object-fit: contain;" alt="Authorized Signatory" />
                      </div>
                      {% else %}
                      <div style="height: 38px;"></div>
                      {% endif %}
                      <div style="font-size: 10px; font-weight: 700; color: #374151; border-top: 1px solid #6B7280; padding-top: 3px; display: inline-block; min-width: 160px;">
                        {{ signatory_label }}
                      </div>
                    </div>"""

if old_mail_sig in mail_html_norm:
    mail_html_norm = mail_html_norm.replace(old_mail_sig, new_mail_sig, 1)
    with open(mail_template_path, "w", encoding="utf-8") as f:
        f.write(mail_html_norm)
    print("payment_receipt.html updated successfully!")
else:
    print("old_mail_sig NOT found in payment_receipt.html")
