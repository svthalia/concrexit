# Generated by Django 4.1.6 on 2023-02-08 19:37

from django.db import migrations
import thumbnails.fields


def create_thumbnail_sources(apps, _):
    Source = apps.get_model("thumbnails", "Source")
    Membergroup = apps.get_model("activemembers", "Membergroup")
    for m in Membergroup.objects.filter(photo__isnull=False).all():
        Source.objects.get_or_create(name=m.photo.name)


class Migration(migrations.Migration):
    dependencies = [
        ("thumbnails", "0001_initial"),
        ("activemembers", "0041_alter_membergroup_photo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="membergroup",
            name="photo",
            field=thumbnails.fields.ImageField(
                blank=True,
                null=True,
                upload_to="committeephotos/",
                verbose_name="Image",
            ),
        ),
        migrations.RunPython(create_thumbnail_sources, migrations.RunPython.noop)
    ]
