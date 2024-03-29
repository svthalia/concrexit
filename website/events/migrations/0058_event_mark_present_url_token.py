# Generated by Django 4.0.7 on 2022-09-07 09:03

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0057_event_mark_present_url_token"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="mark_present_url_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
