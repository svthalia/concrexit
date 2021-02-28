# Generated by Django 3.1.6 on 2021-02-08 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0043_auto_20201215_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='tpay_allowed',
            field=models.BooleanField(default=True, verbose_name='Is Thalia Pay payment allowed for this event'),
        ),
    ]
