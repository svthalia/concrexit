# Generated by Django 3.2.4 on 2021-06-22 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pizzas', '0014_auto_20210509_1311'),
    ]

    operations = [
        migrations.AddField(
            model_name='foodevent',
            name='tpay_allowed',
            field=models.BooleanField(default=True, verbose_name='Allow Thalia Pay'),
        ),
    ]
