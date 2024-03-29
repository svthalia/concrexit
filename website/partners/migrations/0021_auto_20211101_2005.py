# Generated by Django 3.2.8 on 2021-11-01 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0020_auto_20211002_0002'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacancy',
            name='keywords',
            field=models.TextField(blank=True, default='', help_text='Comma separated list of keywords, for example: Django,Python,Concrexit', verbose_name='keywords'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='location',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='location'),
        ),
    ]
