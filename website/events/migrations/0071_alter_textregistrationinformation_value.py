# Generated by Django 5.1.2 on 2024-11-20 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0070_event_update_deadline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textregistrationinformation',
            name='value',
            field=models.TextField(max_length=5000),
        ),
    ]
