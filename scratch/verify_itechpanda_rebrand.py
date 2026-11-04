import os
import sys

def run_audit():
    print("==================================================")
    print("iTechPanda BRANDING & ZERO-BLUR VERIFICATION SUITE")
    print("==================================================")
    
    errors = 0
    
    # 1. Image Assets Check
    print("\n[CHECK 1] Verifying High-Resolution Brand Assets...")
    required_assets = [
        ('CRM/static/images/itechpanda_logo.png', 10000),
        ('CRM/static/images/itechpanda_logo_white.png', 10000),
        ('CRM/static/images/itechpanda_logo.svg', 500),
        ('CRM/static/images/itechpanda_logo_white.svg', 500),
        ('CRM/static/images/itechpanda_symbol.png', 10000),
        ('CRM/static/images/itechpanda_symbol.svg', 500),
        ('CRM/static/images/favicon.png', 1000),
        ('CRM/static/images/favicon.ico', 1000),
    ]
    for path, min_size in required_assets:
        if not os.path.exists(path):
            print(f"  ❌ MISSING: {path}")
            errors += 1
        else:
            sz = os.path.getsize(path)
            if sz < min_size:
                print(f"  ❌ TOO SMALL ({sz} bytes): {path}")
                errors += 1
            else:
                print(f"  ✅ OK ({sz} bytes): {path}")
                
    # 2. Template Inspection for Residual 'DigiPanda'
    print("\n[CHECK 2] Scanning all templates for residual 'digipanda' tokens...")
    residual_templates = []
    for root, _, files in os.walk('CRM/templates'):
        for f in files:
            if f.endswith(('.html', '.txt')):
                p = os.path.join(root, f)
                with open(p, 'r', encoding='utf-8') as fh:
                    txt = fh.read()
                if 'digipanda' in txt.lower():
                    residual_templates.append(p)
                    
    if residual_templates:
        print(f"  ❌ Found {len(residual_templates)} files with residual 'digipanda':")
        for p in residual_templates:
            print(f"     - {p}")
        errors += len(residual_templates)
    else:
        print("  ✅ 0 residual 'digipanda' occurrences found across all HTML & TXT templates!")
        
    # 3. Settings Inspection
    print("\n[CHECK 3] Checking settings.py branding...")
    with open('CRM/config/settings.py', 'r', encoding='utf-8') as f:
        settings_code = f.read()
    if "COMPANY_NAME = os.getenv('COMPANY_NAME', 'iTechPanda CRM')" in settings_code:
        print("  ✅ settings.py COMPANY_NAME is 'iTechPanda CRM'")
    else:
        print("  ❌ settings.py COMPANY_NAME mismatch!")
        errors += 1
        
    if "DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', f\"iTechPanda CRM <{EMAIL_HOST_USER}>\")" in settings_code:
        print("  ✅ settings.py DEFAULT_FROM_EMAIL is 'iTechPanda CRM'")
    else:
        print("  ❌ settings.py DEFAULT_FROM_EMAIL mismatch!")
        errors += 1

    # 4. Context Processor Inspection
    print("\n[CHECK 4] Checking context_processors.py...")
    with open('CRM/accounts/context_processors.py', 'r', encoding='utf-8') as f:
        cp_code = f.read()
    if "'APP_NAME': 'iTechPanda CRM'" in cp_code:
        print("  ✅ accounts/context_processors.py exports APP_NAME = 'iTechPanda CRM'")
    else:
        print("  ❌ accounts/context_processors.py APP_NAME mismatch!")
        errors += 1

    # 5. Constants Inspection
    print("\n[CHECK 5] Checking leads/constants.py...")
    with open('CRM/leads/constants.py', 'r', encoding='utf-8') as f:
        const_code = f.read()
    if "'company_name': 'iTechPanda'" in const_code and "'signatory_label': 'AUTHORISED SIGNATORY FOR iTechPanda'" in const_code:
        print("  ✅ leads/constants.py exports company_name = 'iTechPanda'")
    else:
        print("  ❌ leads/constants.py company_name mismatch!")
        errors += 1

    print("\n==================================================")
    if errors == 0:
        print("VERIFICATION COMPLETE: 100% PASSED! 0 ERRORS.")
        print("==================================================")
        return True
    else:
        print(f"VERIFICATION FAILED: {errors} ERRORS FOUND.")
        print("==================================================")
        return False

if __name__ == '__main__':
    success = run_audit()
    sys.exit(0 if success else 1)
