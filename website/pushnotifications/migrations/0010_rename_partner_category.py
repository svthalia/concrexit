from django.db import migrations


def forwards_func(apps, schema_editor):
    category = apps.get_model("pushnotifications", "Category")
    db_alias = schema_editor.connection.alias

    category.objects.using(db_alias).get(key='sponsor').delete()
    category.objects.create(
        key='partner',
        name_nl='Partners',
        name_en='Partners',
    )


def reverse_func(apps, schema_editor):
    category = apps.get_model("pushnotifications", "Category")
    db_alias = schema_editor.connection.alias

    category.objects.using(db_alias).get(key='partner').delete()
    category.objects.create(
        key='sponsor',
        name_nl='Sponsor',
        name_en='Sponsor',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('pushnotifications', '0009_rename_categories'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
