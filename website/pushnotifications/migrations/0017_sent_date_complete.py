# Generated by Django 2.2.1 on 2019-10-16 17:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pushnotifications', '0016_sent_date_move'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='sent',
        ),
        migrations.RenameField(
            model_name='message',
            old_name='tmp_sent',
            new_name='sent',
        ),
    ]
