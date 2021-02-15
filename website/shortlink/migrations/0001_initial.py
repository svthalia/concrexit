# Generated by Django 3.1.6 on 2021-02-15 20:44

import django.core.validators
from django.db import migrations, models
import re


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ShortLink',
            fields=[
                ('key', models.CharField(help_text='This is what you use after https://thalia.localhost/', max_length=32, primary_key=True, serialize=False, validators=[django.core.validators.RegexValidator(re.compile('^[-a-zA-Z0-9_]+\\Z'), 'Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.', 'invalid')], verbose_name='Name for the url')),
                ('url', models.TextField(help_text='The url the user will be redirected to', validators=[django.core.validators.URLValidator(schemes=['http', 'https'])], verbose_name='Redirection target')),
                ('immediate', models.BooleanField(default=False, help_text='Make sure to only do this when users expect an immediate redirect, if they expect a Thalia site a redirect will be confusing.', verbose_name='Redirect without information page')),
            ],
        ),
    ]
