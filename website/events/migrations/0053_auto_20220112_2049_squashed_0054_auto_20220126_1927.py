# Generated by Django 3.2.11 on 2022-01-26 20:33

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('events', '0053_auto_20220112_2049'), ('events', '0054_auto_20220126_1927')]

    dependencies = [
        ('events', '0052_auto_20211216_2300'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventregistration',
            name='alt_email',
            field=models.EmailField(blank=True, help_text='Email address for non-members', max_length=254, null=True, verbose_name='email'),
        ),
        migrations.AddField(
            model_name='eventregistration',
            name='alt_phone_number',
            field=models.CharField(blank=True, help_text='Phone number for non-members', max_length=20, null=True, validators=[django.core.validators.RegexValidator(message='Please enter a valid phone number', regex='^\\+?\\d+$')], verbose_name='Phone number'),
        ),
    ]
