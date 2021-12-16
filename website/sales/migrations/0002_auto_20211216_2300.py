# Generated by Django 3.2.10 on 2021-12-16 22:00

from decimal import Decimal
import django.core.validators
from django.db import migrations
import payments.models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='discount',
            field=payments.models.PaymentAmountField(blank=True, decimal_places=2, max_digits=8, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00')), payments.models.validate_not_zero], verbose_name='discount'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='total',
            field=payments.models.PaymentAmountField(blank=True, decimal_places=2, help_text='Only when overriding the default', max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.00')), payments.models.validate_not_zero], verbose_name='total'),
        ),
        migrations.AlterField(
            model_name='productlistitem',
            name='price',
            field=payments.models.PaymentAmountField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0), payments.models.validate_not_zero], verbose_name='price'),
        ),
    ]
