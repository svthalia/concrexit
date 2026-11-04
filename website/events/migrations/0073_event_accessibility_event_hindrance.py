from django.db import migrations, models


def set_existing_events_accessible(apps, schema_editor):
    Event = apps.get_model("events", "Event")
    Event.objects.all().update(accessibility=True)


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0072_remove_event_shift"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="accessibility",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Indicate if the event is accessible for people with a "
                    "wheelchair."
                ),
                verbose_name="wheelchair accessible",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="hindrance",
            field=models.TextField(
                blank=True,
                help_text=(
                    "A list of hindrances that might make the event not wheelchair "
                    'accessible. Uses "This event might not be wheelchair accessible '
                    'due to:" as prefix. e.g., "stairs, narrow doors, and uneven '
                    'terrain." '
                ),
                max_length=500,
                null=True,
                verbose_name="hindrance",
            ),
        ),
        migrations.RunPython(
            set_existing_events_accessible,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
