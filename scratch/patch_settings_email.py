settings_path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\config\settings.py'
with open(settings_path, 'r', encoding='utf-8') as f:
    text = f.read()

target = """# Email Configuration (Environment Configurable with Gmail SMTP defaults)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_USE_SSL = False
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'admin@digipandaacademy.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '20'))"""

replacement = """# Email Configuration (Hostinger / Custom SMTP Support with Dynamic SSL/TLS)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.hostinger.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True').lower() in ('true', '1', 'yes')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'admin@digipandaacademy.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', f"DigiPanda Academy <{EMAIL_HOST_USER}>")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '20'))"""

assert target in text, "Target email config block not found in settings.py"
text = text.replace(target, replacement, 1)

with open(settings_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated config/settings.py with Hostinger SMTP & dynamic SSL/TLS successfully!")
