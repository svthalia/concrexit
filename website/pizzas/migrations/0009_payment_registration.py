# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('pizzas', '0008_payment_registration'),
    ]

    def forwards_func(apps, schema_editor):
        Order = apps.get_model('pizzas', 'order')
        Payment = apps.get_model('payments', 'payment')
        db_alias = schema_editor.connection.alias

        for order in Order.objects.using(db_alias).all():
            name = order.name
            if order.member is not None:
                name = '{} {}'.format(order.member.first_name,
                                      order.member.last_name)

            order.payment = Payment.objects.create(
                created_at=order.pizza_event.end,
                type='cash_payment' if order.paid else 'no_payment',
                amount=order.product.price,
                paid_by=order.member,
                processing_date=None,
                notes=(f'Pizza order by {name} '
                       f'for {order.pizza_event.event.title_en}')
            )
            order.save()

    def reverse_func(apps, schema_editor):
        Order = apps.get_model('pizzas', 'order')
        db_alias = schema_editor.connection.alias
        for order in Order.objects.using(db_alias).all():
            payment = order.payment
            order.paid = order.payment.type != 'no_payment'
            order.payment = None
            order.save()
            payment.delete()

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
