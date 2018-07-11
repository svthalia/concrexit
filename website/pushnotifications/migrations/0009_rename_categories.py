from django.db import migrations


def forwards_func(apps, schema_editor):
    category = apps.get_model("pushnotifications", "Category")
    db_alias = schema_editor.connection.alias

    for key in ['general', 'pizza', 'event', 'newsletter',
                'sponsor', 'photo', 'board']:
        cat = category.objects.using(db_alias).get(key=key)
        cat.name_en = cat.name_en.title()
        cat.name_nl = cat.name_nl.title()
        cat.save()


def reverse_func(apps, schema_editor):
    category = apps.get_model("pushnotifications", "Category")
    db_alias = schema_editor.connection.alias

    for key in ['general', 'pizza', 'event', 'newsletter',
                'sponsor', 'photo', 'board']:
        cat = category.objects.using(db_alias).get(key=key)
        cat.name_en = cat.name_en.lower()
        cat.name_nl = cat.name_nl.lower()
        cat.save()


class Migration(migrations.Migration):

    dependencies = [
        ('pushnotifications', '0008_scheduledmessage'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
