# Generated by Django 4.0.4 on 2022-05-18 19:26

from django.db import migrations, models


def migrate_event_organisers(apps, schema_editor):
    Event = apps.get_model("events", "Event")
    for event in Event.objects.all():
        event.organisers.add(event.organiser)
        event.save()

class Migration(migrations.Migration):

    dependencies = [
        ('activemembers', '0040_remove_multilang_field'),
        ('events', '0055_alter_event_no_registration_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='organisers',
            field=models.ManyToManyField(to='activemembers.membergroup',
                                         verbose_name='organisers',
                                         related_name='event_organiser'),
        ),
        migrations.RunPython(migrate_event_organisers),
        migrations.RemoveField(
            model_name='event',
            name='organiser',
        ),
    ]
