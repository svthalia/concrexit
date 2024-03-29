# Generated by Django 4.2.5 on 2023-10-25 11:13

from django.db import migrations
import functools
import thumbnails.fields
import utils.media.services


class Migration(migrations.Migration):
    dependencies = [
        ("merchandise", "0010_alter_merchandiseitem_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="merchandiseitem",
            name="image",
            field=thumbnails.fields.ImageField(
                upload_to=functools.partial(
                    utils.media.services._generic_upload_to,
                    *(),
                    **{"prefix": "merchandise", "token_bytes": 8}
                )
            ),
        ),
    ]
