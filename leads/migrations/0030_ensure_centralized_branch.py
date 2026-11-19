from django.db import migrations


def ensure_centralized_branch(apps, schema_editor):
    Branch = apps.get_model('branches', 'Branch')
    Branch.objects.get_or_create(
        name='Centralized (All Branches)',
        defaults={'status': 'Active'}
    )


def reverse_centralized_branch(apps, schema_editor):
    # We do not delete branch on rollback to prevent accidental cascade
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0029_alter_lead_rating'),
        ('branches', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ensure_centralized_branch, reverse_centralized_branch),
    ]
