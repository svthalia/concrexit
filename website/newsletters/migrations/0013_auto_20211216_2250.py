# Generated by Django 3.2.10 on 2021-12-16 21:50

from django.db import migrations
import payments.models


class Migration(migrations.Migration):

    dependencies = [
        ('newsletters', '0012_remove_multilang_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsletterevent',
            name='penalty_costs',
            field=payments.models.PaymentAmountField(blank=True, decimal_places=2, default=None, help_text='This is the price that a member has to pay when he/she did not show up.', max_digits=8, null=True, validators=[payments.models.validate_not_zero, payments.models.validate_not_zero, payments.models.validate_not_zero], verbose_name='Costs (in Euro)'),
        ),
        migrations.AlterField(
            model_name='newsletterevent',
            name='price',
            field=payments.models.PaymentAmountField(blank=True, decimal_places=2, default=None, max_digits=8, null=True, validators=[payments.models.validate_not_zero, payments.models.validate_not_zero, payments.models.validate_not_zero], verbose_name='Price (in Euro)'),
        ),
    ]
