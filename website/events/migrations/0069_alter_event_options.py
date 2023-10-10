# Generated by Django 4.2.5 on 2023-10-04 16:28

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0068_eventdocument"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="event",
            options={
                "ordering": ("-start",),
                "permissions": (
                    ("override_organiser", "Can access events as if organizing"),
                    ("view_unpublished", "Can see any unpublished event"),
                ),
            },
        ),
    ]