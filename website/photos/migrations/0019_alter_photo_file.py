# Generated by Django 4.1.6 on 2023-02-08 19:37

from django.db import migrations
import photos.models
import thumbnails.fields


def create_thumbnail_sources(apps, _):
    Source = apps.get_model("thumbnails", "Source")
    Photo = apps.get_model("photos", "Photo")
    for photo in Photo.objects.all():
        Source.objects.get_or_create(name=photo.file.name)


class Migration(migrations.Migration):
    dependencies = [
        ("photos", "0018_alter_like_member"),
    ]

    operations = [
        migrations.AlterField(
            model_name="photo",
            name="file",
            field=thumbnails.fields.ImageField(
                upload_to=photos.models.photo_uploadto, verbose_name="file"
            ),
        ),
        migrations.RunPython(create_thumbnail_sources, migrations.RunPython.noop)
    ]
