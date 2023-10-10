# Generated by Django 4.2.7 on 2023-11-15 19:33

from django.db import migrations
import functools
import thumbnails.fields
import utils.media.services


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0047_remove_profile_receive_magazine"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="photo",
            field=thumbnails.fields.ImageField(
                blank=True,
                help_text="Note that your photo may be publicly visible and indexable by search engines in some cases. This happens when you are in a committee with publicly visible members.",
                null=True,
                upload_to=functools.partial(
                    utils.media.services._generic_upload_to,
                    *(),
                    **{"prefix": "avatars", "token_bytes": 16}
                ),
                verbose_name="Photo",
            ),
        ),
    ]