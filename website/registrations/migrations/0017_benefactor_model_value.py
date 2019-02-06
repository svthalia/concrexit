from django.db import migrations


def forwards_func(apps, schema_editor):
    Entry = apps.get_model('registrations', 'entry')
    db_alias = schema_editor.connection.alias
    Entry.objects.using(db_alias).filter(
        membership_type='supporter').update(membership_type='benefactor')


def reverse_func(apps, schema_editor):
    Entry = apps.get_model('registrations', 'entry')
    db_alias = schema_editor.connection.alias
    Entry.objects.using(db_alias).filter(
        membership_type='benefactor').update(membership_type='supporter')


class Migration(migrations.Migration):
    dependencies = [
        ('registrations', '0016_registration_address_country'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
