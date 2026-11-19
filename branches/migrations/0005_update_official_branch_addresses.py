from django.db import migrations

def update_branch_addresses(apps, schema_editor):
    Branch = apps.get_model('branches', 'Branch')
    
    BRANCH_DATA = [
        {
            'name': 'T. Nagar',
            'address': 'Celestial Centre, 2nd Floor, 33 S Usman Road (Near T. Nagar Bus Depot), T. Nagar, Chennai, Tamil Nadu 600017.',
            'phone': '9884678282',
        },
        {
            'name': 'Velachery',
            'address': 'AGS Tower, 3rd Floor, Door No. 35A, Plot No. 74-75, Ganapathy Nagar 1st Street, 100 Feet Bypass Road, Velachery, Chennai, Tamil Nadu 600042.',
            'phone': '9884678282',
        },
        {
            'name': 'Anna Nagar',
            'address': '2nd Floor, 78/6, 3rd Avenue, M Block, Anna Nagar East, Chennai, Tamil Nadu 600102',
            'phone': '9884678282',
        },
        {
            'name': 'Tambaram',
            'address': '18/514, Naru Nagar Main Road, Kadaperi, GST Road, Tambaram, Chennai, Tamil Nadu 600045',
            'phone': '9884678282',
        },
        {
            'name': 'Coimbatore',
            'address': '2nd Floor, 511, Dr Nanjappa Rd, behind HP Petrol Station, Gopalapuram, Gandhipuram, Coimbatore, Tamil Nadu 641018',
            'phone': '9884678282',
        },
        {
            'name': 'Sholinganallur',
            'address': 'Rajiv Gandhi Salai, Pallikoodam Theru, New Kumaran Nagar, Sholinganallur, Chennai, Tamil Nadu 600119',
            'phone': '9884678282',
        },
        {
            'name': 'Porur',
            'address': 'Ground Floor, Door No. 208 & 209, Mount Poonamallee Road, Theru Veedhi Amman Koil Streets, Porur, Chennai, Tamil Nadu 600116',
            'phone': '9884678282',
        },
    ]

    for item in BRANCH_DATA:
        branch, created = Branch.objects.get_or_create(
            name=item['name'],
            defaults={'status': 'Active', 'address': item['address'], 'phone': item['phone']}
        )
        if not created:
            branch.address = item['address']
            if not branch.phone:
                branch.phone = item['phone']
            branch.save(update_fields=['address', 'phone'])

def reverse_update(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('branches', '0004_populate_salesheadbranchaccess'),
    ]

    operations = [
        migrations.RunPython(update_branch_addresses, reverse_update),
    ]
