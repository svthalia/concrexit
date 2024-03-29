# Generated by Django 3.2.3 on 2021-05-17 19:45

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0047_alter_event_shift'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='description_en',
            new_name='description'
        ),
        migrations.RenameField(
            model_name='event',
            old_name='location_en',
            new_name='location'
        ),
        migrations.RenameField(
            model_name='event',
            old_name='no_registration_message_en',
            new_name='no_registration_message'
        ),
        migrations.RenameField(
            model_name='event',
            old_name='title_en',
            new_name='title'
        ),
        migrations.RenameField(
            model_name='registrationinformationfield',
            old_name='description_en',
            new_name='description'
        ),
        migrations.RenameField(
            model_name='registrationinformationfield',
            old_name='name_en',
            new_name='name'
        ),
        migrations.AlterField(
            model_name='event',
            name='description',
            field=tinymce.models.HTMLField(verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='event',
            name='location',
            field=models.CharField(max_length=255, verbose_name='location'),
        ),
        migrations.AlterField(
            model_name='event',
            name='no_registration_message',
            field=models.CharField(blank=True, help_text='Default: No registration required', max_length=200, null=True, verbose_name='message when there is no registration'),
        ),
        migrations.AlterField(
            model_name='event',
            name='title',
            field=models.CharField(max_length=100, verbose_name='title'),
        ),
        migrations.AlterField(
            model_name='registrationinformationfield',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='registrationinformationfield',
            name='name',
            field=models.CharField(max_length=100, verbose_name='field name'),
        ),
    ]
