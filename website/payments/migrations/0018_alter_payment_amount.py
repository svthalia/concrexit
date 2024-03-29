# Generated by Django 3.2.10 on 2021-12-16 22:00

from django.db import migrations
import payments.models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0017_alter_payment_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=payments.models.PaymentAmountField(decimal_places=2, max_digits=8, validators=[payments.models.validate_not_zero], verbose_name='amount'),
        ),
    ]
