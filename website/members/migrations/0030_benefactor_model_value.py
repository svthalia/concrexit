from django.db import migrations


def forwards_func(apps, schema_editor):
    Membership = apps.get_model('members', 'membership')
    db_alias = schema_editor.connection.alias
    Membership.objects.using(db_alias).filter(
        type='supporter').update(type='benefactor')


def reverse_func(apps, schema_editor):
    Membership = apps.get_model('members', 'membership')
    db_alias = schema_editor.connection.alias
    Membership.objects.using(db_alias).filter(
        type='benefactor').update(type='supporter')


class Migration(migrations.Migration):
    dependencies = [
        ('members', '0029_profile_address_country'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
