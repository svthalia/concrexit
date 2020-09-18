from django.db import migrations


def set_created_at(apps, schema_editor):
    """On this migration, set the created at to the processing date."""
    Payment = apps.get_model('payments', 'Payment')
    for payment in Payment.objects.all():
        if payment.processing_date:
            payment.created_at = payment.processing_date
        else:
            payment.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0007_auto_20200510_2042'),
    ]

    operations = [
        migrations.RunPython(set_created_at)
    ]
