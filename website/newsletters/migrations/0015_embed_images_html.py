# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.conf import settings
from django.db import migrations

from newsletters import services


def embed_images_html(_, __):
    cache_dir = os.path.join(settings.MEDIA_ROOT, "newsletters")
    if not os.path.isdir(cache_dir):
        return

    for file in os.listdir(cache_dir):
        with open(os.path.join(cache_dir, file), "r+", encoding="utf-8") as newsletter_file:
            contents = newsletter_file.read()
            new_content = services.embed_linked_html_images(contents)
            newsletter_file.write(new_content)


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ('newsletters', '0014_auto_20211216_2257'),
    ]

    operations = [
        migrations.RunPython(embed_images_html, migrations.RunPython.noop),
    ]
