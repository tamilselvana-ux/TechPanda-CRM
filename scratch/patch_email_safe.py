import re

with open(r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\services\email_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'from email\.mime\.multipart import MIMEMultipart.*?img\.add_header\(\'Content-Disposition\', \'inline\', filename=f\'\{cid\}\.png\'\)\r?\n\s+root\.attach\(img\)'

replacement = """from django.core.mail.message import SafeMIMEMultipart, SafeMIMEText
        from email.mime.image import MIMEImage
        from email.mime.application import MIMEApplication
        from django.core.mail import EmailMessage

        if attachments:
            root = SafeMIMEMultipart('mixed')
            related = SafeMIMEMultipart('related')
            alt = SafeMIMEMultipart('alternative')
            alt.attach(SafeMIMEText(text_body, 'plain', 'utf-8'))
            alt.attach(SafeMIMEText(html_body, 'html', 'utf-8'))
            related.attach(alt)
            if inline_images:
                for cid, data, mime_type in inline_images:
                    subtype = mime_type.split('/')[-1] if '/' in mime_type else 'png'
                    img = MIMEImage(data, _subtype=subtype)
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=f'{cid}.png')
                    related.attach(img)
            root.attach(related)
            for fname, data, mime_type in attachments:
                part = MIMEApplication(data)
                part.add_header('Content-Disposition', 'attachment', filename=fname)
                root.attach(part)
        else:
            root = SafeMIMEMultipart('related')
            alt = SafeMIMEMultipart('alternative')
            alt.attach(SafeMIMEText(text_body, 'plain', 'utf-8'))
            alt.attach(SafeMIMEText(html_body, 'html', 'utf-8'))
            root.attach(alt)
            if inline_images:
                for cid, data, mime_type in inline_images:
                    subtype = mime_type.split('/')[-1] if '/' in mime_type else 'png'
                    img = MIMEImage(data, _subtype=subtype)
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=f'{cid}.png')
                    root.attach(img)"""

new_content, count = re.subn(pattern, replacement, content, count=1, flags=re.DOTALL)
print('Replacements made:', count)

if count > 0:
    with open(r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\services\email_service.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Updated successfully!')
