# Generated by Django 4.1.4 on 2023-02-02 08:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0064_remove_event_slide"),
        ("announcements", "0014_slide_linked_event"),
    ]

    operations = [
        migrations.RenameField(
            model_name="slide",
            old_name="linked_event",
            new_name="event",
        ),
        migrations.AlterField(
            model_name="slide",
            name="event",
            field=models.OneToOneField(
                blank=True,
                help_text="This event's header image will be changed to this slide.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="slide",
                to="events.event",
            ),
        ),
    ]