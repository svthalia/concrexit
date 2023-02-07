# Generated by Django 4.1.6 on 2023-02-06 19:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0064_remove_event_registration_reminder_and_more"),
        ("pushnotifications", "0025_registrationreminder_eventstartreminder"),
    ]

    operations = [
        migrations.AlterField(
            model_name="registrationreminder",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="registration_reminder",
                to="events.event",
            ),
        ),
        migrations.AlterField(
            model_name="registrationreminder",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="start_reminder",
                to="events.event",
            ),
        ),
    ]
