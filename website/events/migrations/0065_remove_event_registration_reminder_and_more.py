# Generated by Django 4.1.7 on 2023-03-15 18:46

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0064_remove_event_slide"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="event",
            name="registration_reminder",
        ),
        migrations.RemoveField(
            model_name="event",
            name="start_reminder",
        ),
    ]
