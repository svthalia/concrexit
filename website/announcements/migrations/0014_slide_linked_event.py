# Generated by Django 4.1.4 on 2023-02-02 07:56

from django.db import migrations, models
import django.db.models.deletion


def populate_slide_linked_event(apps, schema_editor):
    """Populate the new Slide.linked_event based on Event.slide."""

    Event = apps.get_model("events", "Event")
    Slide = apps.get_model("announcements", "Slide")

    events = list(Event.objects.filter(slide__isnull=False).select_related("slide"))
    slides = []
    for event in events:
        event.slide.linked_event = event
        slides.append(event.slide)

    # If slides contains duplicates, bulk_update only updates the first occurrence.
    Slide.objects.bulk_update(slides, ["linked_event"], batch_size=100)


class Migration(migrations.Migration):

    dependencies = [
        ("announcements", "0013_alter_slide_content"),
    ]

    run_before = [("events", "0064_remove_event_slide")]

    operations = [
        migrations.AddField(
            model_name="slide",
            name="linked_event",
            field=models.OneToOneField(
                blank=True,
                help_text="This event's header image will be changed to this slide.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="linked_slide",
                to="events.event",
            ),
        ),
        migrations.RunPython(
            populate_slide_linked_event,
            reverse_code=migrations.RunPython.noop,
            elidable=True,
        ),
    ]
