# Generated by Django 4.2.6 on 2023-11-01 18:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("promotion", "0004_promotionchannel_publisher_reminder_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="promotionrequest",
            name="status_updated",
            field=models.BooleanField(default=False, verbose_name="status updated"),
        ),
    ]
