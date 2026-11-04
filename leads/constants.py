"""
Constants and centralized configurations for DigiPanda CRM.
"""

DIGIPANDA_INVOICE_CONFIG = {
    'company_name': 'iTechPanda',
    'company_legal_name': 'iTechPanda Software Training Private Limited',
    'address_lines': [
        '2nd Floor, No 15, Sy No 33,34A,35, Celestial Complex',
        'South Usman Road, T Nagar, Chennai, Tamil Nadu, 600017'
    ],
    'address_single_line': '2nd Floor, No 15, Sy No 33,34A,35, Celestial Complex, South Usman Road, T Nagar, Chennai, Tamil Nadu, 600017',
    'mobile': '9884678282',
    'gstin': '33EECPS1311N1ZJ',
        'email': 'admin@itechpanda.com',
    'website': 'www.itechpanda.com',
    'default_place_of_supply': 'Tamil Nadu',
    'bank_details': {
        'name': 'iTechPanda Software Training Private Limited',
        'ifsc': 'HDFC0000141',
        'account_number': '50200115357040',
        'bank_name': 'HDFC Bank, CHENNAI - R A PURAM',
    },
    'terms_and_conditions': [
        'Enrollment and Fees: Fees once paid for the training program are non-refundable and non-transferable under any circumstances.',
        'Course Access: Access to course materials, online platforms, and software licenses is granted for the duration of the course only and may not be shared with others.'
    ],
    'signatory_label': 'AUTHORISED SIGNATORY FOR iTechPanda'
}

# Backward compatibility alias
TECHPANDA_INVOICE_CONFIG = DIGIPANDA_INVOICE_CONFIG
