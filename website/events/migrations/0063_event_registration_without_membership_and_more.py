# Generated by Django 4.1.5 on 2023-01-25 20:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0041_alter_profile_photo"),
        ("events", "0062_alter_event_registration_msg_cancelled_late_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="registration_without_membership",
            field=models.BooleanField(
                default=False,
                help_text="Users without a currently active membership (such as past members) are allowed to register for this event. This is useful for events aimed at alumni, for example.",
                verbose_name="registration without membership",
            ),
        ),
        migrations.AlterField(
            model_name="eventregistration",
            name="member",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="members.member",
            ),
        ),
    ]
