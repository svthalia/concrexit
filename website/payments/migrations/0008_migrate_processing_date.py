from django.db import migrations


def set_created_at(apps, schema_editor):
    """On this migration, set the created at to the processing date."""
    Payment = apps.get_model('payments', 'Payment')
    for payment in Payment.objects.all():
        if payment.processing_date:
            payment.created_at = payment.processing_date
        else:
            if hasattr(payment, 'pizzas_order'):
                order = payment.pizzas_order
                order.payment = None
                order.save()

            if hasattr(payment, 'registrations_entry'):
                entry = payment.registrations_entry
                entry.payment = None
                entry.save()

            payment.delete()


def set_processed_date(apps, schema_editor):
    """Revert sets the processing date to the created_at value."""
    Payment = apps.get_model('payments', 'Payment')
    for payment in Payment.objects.all():
        payment.processing_date = payment.created_at


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0007_auto_20200510_2042'),
    ]

    operations = [
        migrations.RunPython(set_created_at, set_processed_date)
    ]
