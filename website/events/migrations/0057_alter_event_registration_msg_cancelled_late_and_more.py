# Generated by Django 4.0.7 on 2022-09-07 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0056_event_registration_msg_cancelled_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='registration_msg_cancelled_late',
            field=models.CharField(blank=True, help_text='Default: Your registration is cancelled after the deadline and you will pay a fine of €{fine}', max_length=200, null=True, verbose_name='message when user cancelled their registration late and will pay a fine'),
        ),
        migrations.AlterField(
            model_name='event',
            name='registration_msg_waitinglist',
            field=models.CharField(blank=True, help_text='Default: You are in queue position {pos}', max_length=200, null=True, verbose_name='message when user is on the waiting list'),
        ),
    ]
