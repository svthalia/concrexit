# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-16 09:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('merchandise', '0002_auto_20160805_1730'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='merchandiseitem',
            name='description',
        ),
        migrations.RemoveField(
            model_name='merchandiseitem',
            name='name',
        ),
        migrations.AddField(
            model_name='merchandiseitem',
            name='description_en',
            field=models.TextField(default='', verbose_name='description (EN)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='merchandiseitem',
            name='description_nl',
            field=models.TextField(default='', verbose_name='description (NL)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='merchandiseitem',
            name='name_en',
            field=models.CharField(default='', max_length=200, verbose_name='name (EN)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='merchandiseitem',
            name='name_nl',
            field=models.CharField(default='', max_length=200, verbose_name='name (NL)'),
            preserve_default=False,
        ),
    ]
