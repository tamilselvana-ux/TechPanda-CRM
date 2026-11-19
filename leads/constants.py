"""
Constants and centralized configurations for DigiPanda CRM.
"""

DIGIPANDA_INVOICE_CONFIG = {
    'company_name': 'DigiPanda',
    'company_legal_name': 'DigiPanda Software Training Private Limited',
    'address_lines': [
        '2nd Floor, No 15, Sy No 33,34A,35, Celestial Complex',
        'South Usman Road, T Nagar, Chennai, Tamil Nadu, 600017'
    ],
    'address_single_line': '2nd Floor, No 15, Sy No 33,34A,35, Celestial Complex, South Usman Road, T Nagar, Chennai, Tamil Nadu, 600017',
    'mobile': '9884678282',
    'gstin': '33EECPS1311N1ZJ',
        'email': 'admin@digipandaacademy.com',
    'website': 'www.digipandaacademy.com',
    'default_place_of_supply': 'Tamil Nadu',
    'bank_details': {
        'name': 'DigiPanda Software Training Private Limited',
        'ifsc': 'HDFC0000141',
        'account_number': '50200115357040',
        'bank_name': 'HDFC Bank, CHENNAI - R A PURAM',
    },
    'terms_and_conditions': [
        'Enrollment and Fees: Fees once paid for the training program are non-refundable and non-transferable under any circumstances.',
        'Course Access: Access to course materials, online platforms, and software licenses is granted for the duration of the course only and may not be shared with others.'
    ],
    'signatory_label': 'AUTHORISED SIGNATORY FOR DigiPanda'
}

# Backward compatibility alias
TECHPANDA_INVOICE_CONFIG = DIGIPANDA_INVOICE_CONFIG

# Canonical branch directory from official TechPanda Branches Master
TECHPANDA_BRANCH_ADDRESSES = {
    't_nagar': {
        'name': 'T. Nagar (Main Branch)',
        'aliases': ['t nagar', 't. nagar', 't.nagar', 't-nagar', 'main branch', 'corporate hq', 'central'],
        'address_lines': [
            'Celestial Centre, 2nd Floor, 33 S Usman Road (Near T. Nagar Bus Depot)',
            'T. Nagar, Chennai, Tamil Nadu 600017'
        ],
        'full_address': 'Celestial Centre, 2nd Floor, 33 S Usman Road (Near T. Nagar Bus Depot), T. Nagar, Chennai, Tamil Nadu 600017.',
        'city': 'Chennai',
        'pincode': '600017',
        'phone': '9884678282',
    },
    'velachery': {
        'name': 'Velachery',
        'aliases': ['velachery', 'velachary'],
        'address_lines': [
            'AGS Tower, 3rd Floor, Door No. 35A, Plot No. 74-75, Ganapathy Nagar 1st Street',
            '100 Feet Bypass Road, Velachery, Chennai, Tamil Nadu 600042'
        ],
        'full_address': 'AGS Tower, 3rd Floor, Door No. 35A, Plot No. 74-75, Ganapathy Nagar 1st Street, 100 Feet Bypass Road, Velachery, Chennai, Tamil Nadu 600042.',
        'city': 'Chennai',
        'pincode': '600042',
        'phone': '9884678282',
    },
    'anna_nagar': {
        'name': 'Anna Nagar',
        'aliases': ['anna nagar', 'annanagar', 'anna-nagar'],
        'address_lines': [
            '2nd Floor, 78/6, 3rd Avenue, M Block',
            'Anna Nagar East, Chennai, Tamil Nadu 600102'
        ],
        'full_address': '2nd Floor, 78/6, 3rd Avenue, M Block, Anna Nagar East, Chennai, Tamil Nadu 600102',
        'city': 'Chennai',
        'pincode': '600102',
        'phone': '9884678282',
    },
    'tambaram': {
        'name': 'Tambaram',
        'aliases': ['tambaram', 'kadaperi'],
        'address_lines': [
            '18/514, Naru Nagar Main Road, Kadaperi',
            'GST Road, Tambaram, Chennai, Tamil Nadu 600045'
        ],
        'full_address': '18/514, Naru Nagar Main Road, Kadaperi, GST Road, Tambaram, Chennai, Tamil Nadu 600045',
        'city': 'Chennai',
        'pincode': '600045',
        'phone': '9884678282',
    },
    'coimbatore': {
        'name': 'Coimbatore',
        'aliases': ['coimbatore', 'kovai', 'gandhipuram'],
        'address_lines': [
            '2nd Floor, 511, Dr Nanjappa Rd, behind HP Petrol Station',
            'Gopalapuram, Gandhipuram, Coimbatore, Tamil Nadu 641018'
        ],
        'full_address': '2nd Floor, 511, Dr Nanjappa Rd, behind HP Petrol Station, Gopalapuram, Gandhipuram, Coimbatore, Tamil Nadu 641018',
        'city': 'Coimbatore',
        'pincode': '641018',
        'phone': '9884678282',
    },
    'sholinganallur': {
        'name': 'Sholinganallur (OMR)',
        'aliases': ['sholinganallur', 'omr', 'sholinganallur (omr)'],
        'address_lines': [
            'Rajiv Gandhi Salai, Pallikoodam Theru',
            'New Kumaran Nagar, Sholinganallur, Chennai, Tamil Nadu 600119'
        ],
        'full_address': 'Rajiv Gandhi Salai, Pallikoodam Theru, New Kumaran Nagar, Sholinganallur, Chennai, Tamil Nadu 600119',
        'city': 'Chennai',
        'pincode': '600119',
        'phone': '9884678282',
    },
    'porur': {
        'name': 'Porur',
        'aliases': ['porur', 'mount poonamallee'],
        'address_lines': [
            'Ground Floor, Door No. 208 & 209, Mount Poonamallee Road',
            'Theru Veedhi Amman Koil Streets, Porur, Chennai, Tamil Nadu 600116'
        ],
        'full_address': 'Ground Floor, Door No. 208 & 209, Mount Poonamallee Road, Theru Veedhi Amman Koil Streets, Porur, Chennai, Tamil Nadu 600116',
        'city': 'Chennai',
        'pincode': '600116',
        'phone': '9884678282',
    },
}

def resolve_branch_address(branch):
    """
    Returns a dict with:
      - branch_name: formatted branch name
      - address_lines: list of 2 formatted lines
      - full_address: complete single-line address
      - phone: contact phone number
    Checks database branch.address first; if blank or missing, matches against canonical addresses.
    Falls back gracefully to T. Nagar (Main Branch).
    """
    default_branch_info = TECHPANDA_BRANCH_ADDRESSES['t_nagar']

    if not branch:
        return {
            'branch_name': default_branch_info['name'],
            'address_lines': list(default_branch_info['address_lines']),
            'full_address': default_branch_info['full_address'],
            'phone': default_branch_info['phone'],
        }

    raw_name = (branch.name or '').strip().lower()

    # Match by key or alias
    matched_canonical = None
    for key, data in TECHPANDA_BRANCH_ADDRESSES.items():
        if raw_name == key or any(alias in raw_name for alias in data['aliases']):
            matched_canonical = data
            break

    # If database branch already has an address entered
    db_address = (getattr(branch, 'address', '') or '').strip()
    if db_address:
        # Split into lines if comma or newline separated
        if '\n' in db_address:
            lines = [l.strip() for l in db_address.split('\n') if l.strip()]
        elif ',' in db_address:
            parts = [p.strip() for p in db_address.split(',') if p.strip()]
            if len(parts) >= 4:
                half = len(parts) // 2
                lines = [', '.join(parts[:half]), ', '.join(parts[half:])]
            else:
                lines = [db_address]
        else:
            lines = [db_address]

        return {
            'branch_name': branch.name,
            'address_lines': lines,
            'full_address': db_address,
            'phone': branch.phone or (matched_canonical['phone'] if matched_canonical else default_branch_info['phone']),
        }

    # Use matched canonical if DB address was blank
    if matched_canonical:
        return {
            'branch_name': branch.name or matched_canonical['name'],
            'address_lines': list(matched_canonical['address_lines']),
            'full_address': matched_canonical['full_address'],
            'phone': branch.phone or matched_canonical['phone'],
        }

    # Fallback default
    return {
        'branch_name': branch.name or default_branch_info['name'],
        'address_lines': list(default_branch_info['address_lines']),
        'full_address': default_branch_info['full_address'],
        'phone': branch.phone or default_branch_info['phone'],
    }

