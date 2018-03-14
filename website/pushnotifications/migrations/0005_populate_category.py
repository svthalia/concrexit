# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forwards_func(apps, schema_editor):
    Category = apps.get_model("pushnotifications", "Category")
    db_alias = schema_editor.connection.alias
    Category.objects.using(db_alias).bulk_create([
        Category(key="general", name_en="general", name_nl="algemeen"),
        Category(key="pizza", name_en="pizza", name_nl="pizza"),
        Category(key="event", name_en="event", name_nl="evenement"),
        Category(key="newsletter", name_en="newsletter", name_nl="nieuwsbrief"),
        Category(key="sponsor", name_en="sponsor", name_nl="sponsor"),
        Category(key="photo", name_en="photo", name_nl="foto"),
        Category(key="board", name_en="board", name_nl="bestuur"),
    ])

    Device = apps.get_model("pushnotifications", "Device")
    for device in Device.objects.using(db_alias).all():
        for category in Category.objects.using(db_alias).all():
            device.receive_category.add(category)


def reverse_func(apps, schema_editor):
    Category = apps.get_model("pushnotifications", "Category")
    db_alias = schema_editor.connection.alias
    Category.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pushnotifications', '0004_auto_20180221_1924'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
