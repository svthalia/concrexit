# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

MIGRATION_MAP = {
    'drinks': 'leisure',
    'activity': 'other',
    'generalmeeting': 'association',
    'workshop': 'education',
    'lunchlecture': 'education',
    'party': 'leisure'
}


def forwards_func(apps, schema_editor):
    Event = apps.get_model('events', 'event')
    db_alias = schema_editor.connection.alias
    for cat, val in MIGRATION_MAP.items():
        for e in Event.objects.using(db_alias).filter(category=cat):
            e.category = val
            e.save()


def reverse_func(apps, schema_editor):
    Event = apps.get_model('events', 'event')
    db_alias = schema_editor.connection.alias
    for cat, val in MIGRATION_MAP.items():
        for e in Event.objects.using(db_alias).filter(category=val):
            e.category = cat
            e.save()


class Migration(migrations.Migration):
    dependencies = [
        ('events', '0035_registration_payment_obj'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
