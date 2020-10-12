# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-22 19:59
from __future__ import unicode_literals
import hashlib

from django.db import migrations, models


def add_digests(apps, schema_editor):
    # pylint: disable=cell-var-from-loop
    Photo = apps.get_model('photos', 'Photo')
    for photo in Photo.objects.all():
        hash_sha1 = hashlib.sha1()
        for chunk in iter(lambda: photo.file.read(4096), b""):
            hash_sha1.update(chunk)
        photo._digest = hash_sha1.hexdigest()
        photo.save()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('photos', '0007_auto_20170218_2142'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='_digest',
            field=models.CharField(blank=True, default='', max_length=40, verbose_name='digest'),
            preserve_default=False,
        ),
        migrations.RunPython(
            code=add_digests,
        ),
        migrations.AlterField(
            model_name='Photo',
            name='_digest',
            field=models.CharField(max_length=40, verbose_name='digest'),
        ),
    ]
