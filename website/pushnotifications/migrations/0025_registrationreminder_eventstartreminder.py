# Generated by Django 4.1.6 on 2023-02-06 18:38

import django.db.models.deletion
from django.db import migrations, models


def populate_event_start_reminder(apps, schema_editor):
    Event = apps.get_model("events", "Event")
    EventStartReminder = apps.get_model("pushnotifications", "EventStartReminder")

    # Ensure that only one EventStartReminder
    # is made for each old ScheduledMessage.
    messages = set()
    for event in Event.objects.filter(
        registration_reminder__isnull=False
    ).select_related("start_reminder"):
        if event.start_reminder.pk in messages:
            continue

        messages.add(event.start_reminder.pk)
        EventStartReminder(
            event=event,
            scheduledmessage_ptr=event.start_reminder,
        ).save_base(raw=True)


def populate_registration_reminder(apps, schema_editor):
    Event = apps.get_model("events", "Event")
    RegistrationReminder = apps.get_model("pushnotifications", "RegistrationReminder")

    # Ensure that only one RegistrationReminder
    # is made for each old ScheduledMessage.
    messages = set()
    for event in Event.objects.filter(
        registration_reminder__isnull=False
    ).select_related("registration_reminder"):
        if event.registration_reminder.pk in messages:
            continue

        messages.add(event.registration_reminder.pk)
        RegistrationReminder(
            event=event,
            scheduledmessage_ptr=event.registration_reminder,
        ).save_base(raw=True)


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0064_remove_event_slide"),
        ("pushnotifications", "0024_alter_foodorderremindermessage_food_event"),
    ]

    run_before = [
        ("events", "0065_remove_event_registration_reminder_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RegistrationReminder",
            fields=[
                (
                    "scheduledmessage_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="pushnotifications.scheduledmessage",
                    ),
                ),
                (
                    "event",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="temp_registration_reminder",
                        to="events.event",
                    ),
                ),
            ],
            bases=("pushnotifications.scheduledmessage",),
        ),
        migrations.CreateModel(
            name="EventStartReminder",
            fields=[
                (
                    "scheduledmessage_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="pushnotifications.scheduledmessage",
                    ),
                ),
                (
                    "event",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="temp_start_reminder",
                        to="events.event",
                    ),
                ),
            ],
            bases=("pushnotifications.scheduledmessage",),
        ),
        migrations.RunPython(
            populate_event_start_reminder, migrations.RunPython.noop, elidable=True
        ),
        migrations.RunPython(
            populate_registration_reminder, migrations.RunPython.noop, elidable=True
        ),
    ]
