import os

from django.conf import settings
from django.db import migrations


def make_public_thabloids_private(apps, schema_editor):
    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, "private/thabloids/")):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, "private/thabloids/"))

    os.rename(os.path.join(settings.MEDIA_ROOT, "public/thabloids/"),os.path.join(settings.MEDIA_ROOT, "private/thabloids/"))

    Thabloid = apps.get_model('thabloid', 'Thabloid')
    db_alias = schema_editor.connection.alias
    for thabloid in Thabloid.objects.using(db_alias).all():
        thabloid.file.name = os.path.join("private/thabloids", os.path.basename(thabloid.file.name))
        thabloid.save()

def make_public_thabloids_public(apps, schema_editor):
    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, "public/thabloids/")):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, "public/thabloids/"))

    os.rename(os.path.join(settings.MEDIA_ROOT, "private/thabloids/"),os.path.join(settings.MEDIA_ROOT, "public/thabloids/"))

    Thabloid = apps.get_model('thabloid', 'Thabloid')
    db_alias = schema_editor.connection.alias
    for thabloid in Thabloid.objects.using(db_alias).all():
        thabloid.file.name = os.path.join("public/thabloids", os.path.basename(thabloid.file.name))
        thabloid.save()


class Migration(migrations.Migration):

    dependencies = [
        ('thabloid', '0005_auto_20190516_1536'),
    ]

    operations = [
        migrations.RunPython(make_public_thabloids_private, make_public_thabloids_public)
    ]
