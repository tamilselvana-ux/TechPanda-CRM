with open(r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\services\email_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_addr,
            to=[recipient],
        )
        if inline_images:
            message.mixed_subtype = 'related'
        message.attach_alternative(html_body, "text/html")
        if attachments:
            for att in attachments:
                message.attach(*att)
        if inline_images:
            from email.mime.image import MIMEImage
            for cid, img_data, mime_type in inline_images:
                mime_img = MIMEImage(img_data)
                mime_img.add_header('Content-ID', f'<{cid}>')
                mime_img.add_header('Content-Disposition', 'inline', filename=f'{cid}.png')
                message.attach(mime_img)
        message.send(fail_silently=False)
        return True, "Email dispatched successfully\""""

new_block = """        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.image import MIMEImage
        from email.mime.application import MIMEApplication
        from django.core.mail import EmailMessage

        if attachments:
            root = MIMEMultipart('mixed')
            related = MIMEMultipart('related')
            alt = MIMEMultipart('alternative')
            alt.attach(MIMEText(text_body, 'plain', 'utf-8'))
            alt.attach(MIMEText(html_body, 'html', 'utf-8'))
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
            root = MIMEMultipart('related')
            alt = MIMEMultipart('alternative')
            alt.attach(MIMEText(text_body, 'plain', 'utf-8'))
            alt.attach(MIMEText(html_body, 'html', 'utf-8'))
            root.attach(alt)
            if inline_images:
                for cid, data, mime_type in inline_images:
                    subtype = mime_type.split('/')[-1] if '/' in mime_type else 'png'
                    img = MIMEImage(data, _subtype=subtype)
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=f'{cid}.png')
                    root.attach(img)

        root['Subject'] = subject
        root['From'] = from_addr
        root['To'] = recipient

        class CustomMIMEEmail(EmailMessage):
            def __init__(self, mime_msg, to, from_email):
                super().__init__(to=to, from_email=from_email)
                self._mime_msg = mime_msg

            def message(self):
                return self._mime_msg

        custom_email = CustomMIMEEmail(root, to=[recipient], from_email=from_addr)
        custom_email.send(fail_silently=False)
        return True, "Email dispatched successfully\""""

content_norm = content.replace('\r\n', '\n')
old_block_norm = old_block.replace('\r\n', '\n').strip()
new_block_norm = new_block.replace('\r\n', '\n').strip()

if old_block_norm in content_norm:
    content_norm = content_norm.replace(old_block_norm, new_block_norm)
    with open(r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\services\email_service.py', 'w', encoding='utf-8') as f:
        f.write(content_norm.replace('\n', '\r\n'))
    print("Replaced successfully!")
else:
    print("Old block not found!")
