# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-03 16:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0013_auto_20170215_2148'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ('-start',), 'permissions': (('override_organiser', 'Can access events as if organizing'),)},
        ),
    ]
