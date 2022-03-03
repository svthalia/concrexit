# Generated by Django 3.2.10 on 2021-12-16 21:50

from django.db import migrations
import payments.models


class Migration(migrations.Migration):

    dependencies = [
        ('merchandise', '0005_remove_multilang_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='merchandiseitem',
            name='price',
            field=payments.models.PaymentAmountField(decimal_places=2, max_digits=8, validators=[payments.models.validate_not_zero, payments.models.validate_not_zero, payments.models.validate_not_zero]),
        ),
    ]
