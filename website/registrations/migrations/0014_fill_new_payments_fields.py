from django.db import migrations


def forwards_func(apps, schema_editor):
    Entry = apps.get_model('registrations', 'entry')
    Renewal = apps.get_model('registrations', 'renewal')
    db_alias = schema_editor.connection.alias
    for entry in Entry.objects.using(db_alias).all():
        if entry.payment and entry.membership:
            payment = entry.payment
            membership = entry.membership
            payment.paid_by = membership.user
            payment.notes = 'Membership registration'
            try:
                renewal = entry.renewal
                payment.notes = 'Membership renewal'
            except Renewal.DoesNotExist:
                pass
            payment.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('registrations', '0013_auto_20181114_2104'),
        ('payments', '0002_auto_20181127_1819')
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
