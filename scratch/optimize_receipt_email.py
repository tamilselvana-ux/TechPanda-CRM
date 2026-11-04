import os

# 1. Update templates/emails/payment_receipt.html
html_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\emails\payment_receipt.html'
with open(html_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace header logo block
old_logo_block = """                    <div style="margin-bottom: 6px;">
                      <img src="{% if logo_data_uri %}{{ logo_data_uri }}{% else %}https://digipanda.org/static/images/digipanda_logo.png{% endif %}" height="36" style="height: 36px; width: auto; max-width: 140px; display: block; border: none;" alt="DigiPanda" />
                    </div>"""

new_logo_block = """                    <div style="margin-bottom: 8px;">
                      {% if logo_cid %}
                      <img src="cid:{{ logo_cid }}" height="36" style="height: 36px; width: auto; max-width: 150px; display: block; border: none;" alt="DigiPanda" />
                      {% else %}
                      <div style="font-size: 26px; font-weight: 800; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; letter-spacing: -0.5px; line-height: 1.1;">
                        <span style="color: #0284c7;">digi</span><span style="color: #16a34a;">panda</span><span style="font-size: 11px; font-weight: 700; color: #64748b; background: #e2e8f0; padding: 2px 6px; border-radius: 4px; margin-left: 6px; vertical-align: middle; letter-spacing: 0.5px;">ACADEMY</span>
                      </div>
                      {% endif %}
                    </div>"""

assert old_logo_block in text, "old_logo_block not found in payment_receipt.html"
text = text.replace(old_logo_block, new_logo_block, 1)

# Replace signatory block
old_sig_block = """                    <!-- Signatory -->
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

new_sig_block = """                    <!-- Signatory -->
                    <div align="right" style="margin-top: 18px; text-align: right;">
                      {% if signature_cid %}
                      <div style="margin-bottom: -6px;">
                        <img src="cid:{{ signature_cid }}" width="140" height="36" style="width: 140px; height: 36px; display: inline-block; border: none; object-fit: contain;" alt="Authorized Signatory" />
                      </div>
                      {% elif is_authorized %}
                      <div style="font-family: 'Brush Script MT', cursive, sans-serif; font-size: 22px; color: #1e3a8a; margin-bottom: -4px;">
                        Shashikala.K
                      </div>
                      {% else %}
                      <div style="height: 36px;"></div>
                      {% endif %}
                      <div style="font-size: 10px; font-weight: 700; color: #374151; border-top: 1px solid #6B7280; padding-top: 3px; display: inline-block; min-width: 160px;">
                        {{ signatory_label }}
                      </div>
                    </div>"""

assert old_sig_block in text, "old_sig_block not found in payment_receipt.html"
text = text.replace(old_sig_block, new_sig_block, 1)

# Update footer email address
text = text.replace("email admin@digipanda.com", "email admin@digipandaacademy.com")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated payment_receipt.html successfully!")


# 2. Update services/email_service.py to attach CID inline images and exclude heavy base64 strings
svc_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\services\email_service.py'
with open(svc_path, 'r', encoding='utf-8') as f:
    svc_text = f.read()

old_att_block = """        pdf_ctx = get_receipt_context(req, payment)
        context.update(pdf_ctx)

        qr_png_bytes = pdf_ctx.get('qr_png_bytes')
        if qr_png_bytes:
            inline_images.append(('receipt_qr_code', qr_png_bytes, 'image/png'))

        pdf_bytes = generate_receipt_pdf(pdf_ctx)
        if pdf_bytes:
            filename = f"DigiPanda_Receipt_{payment.receipt_number}.pdf"
            attachments.append((filename, pdf_bytes, "application/pdf"))"""

new_att_block = """        pdf_ctx = get_receipt_context(req, payment)
        context.update(pdf_ctx)
        # Clear heavy base64 strings for email payload to stay < 20 KB (avoids Gmail clipping)
        context['logo_data_uri'] = None
        context['signature_data_uri'] = None

        # Attach signature as lightweight inline CID image if available
        sig_file = os.path.join(settings.BASE_DIR, 'static', 'images', 'shashi_sign.png')
        if not os.path.exists(sig_file):
            sig_file = os.path.join(settings.BASE_DIR, 'static', 'images', 'authorized_signature.png')
        if os.path.exists(sig_file):
            try:
                with open(sig_file, 'rb') as sf:
                    sig_bytes = sf.read()
                inline_images.append(('receipt_signature', sig_bytes, 'image/png'))
                context['signature_cid'] = 'receipt_signature'
            except Exception:
                context['signature_cid'] = None

        # Generate official PDF attachment (which has the complete invoice, QR code & signature)
        pdf_bytes = generate_receipt_pdf(pdf_ctx)
        if pdf_bytes:
            filename = f"DigiPanda_Receipt_{payment.receipt_number}.pdf"
            attachments.append((filename, pdf_bytes, "application/pdf"))"""

assert old_att_block in svc_text, "old_att_block not found in email_service.py"
svc_text = svc_text.replace(old_att_block, new_att_block, 1)

with open(svc_path, 'w', encoding='utf-8') as f:
    f.write(svc_text)

print("Updated services/email_service.py successfully!")
