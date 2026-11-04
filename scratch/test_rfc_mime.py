import os, sys
sys.path.insert(0, r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from django.core.mail import EmailMessage

def build_mime_message(subject, text_body, html_body, from_addr, to_addrs, inline_images=None, attachments=None):
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
    root['To'] = ', '.join(to_addrs)
    return root

msg = build_mime_message('Test Subj', 'text', '<html>hi<img src="cid:logo"></html>', 'admin@digipandaacademy.com', ['test@example.com'], inline_images=[('logo', b'fake_data', 'image/png')], attachments=[('invoice.pdf', b'pdf_data', 'application/pdf')])

def print_tree(part, indent=0):
    print('  '*indent + f"Content-Type: {part.get_content_type()} (ID: {part.get('Content-ID')}, Disp: {part.get('Content-Disposition')})")
    if part.is_multipart():
        for sub in part.get_payload():
            print_tree(sub, indent+1)

print_tree(msg)
