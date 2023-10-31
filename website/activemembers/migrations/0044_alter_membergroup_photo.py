# Generated by Django 4.2.5 on 2023-10-25 11:13

from django.db import migrations
import functools
import thumbnails.fields
import utils.media.services


class Migration(migrations.Migration):
    dependencies = [
        ("activemembers", "0043_membergroup_chair_permissions_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="membergroup",
            name="photo",
            field=thumbnails.fields.ImageField(
                blank=True,
                null=True,
                upload_to=functools.partial(
                    utils.media.services._generic_upload_to,
                    *(),
                    **{"prefix": "committeephotos", "token_bytes": 8}
                ),
                verbose_name="Image",
            ),
        ),
    ]