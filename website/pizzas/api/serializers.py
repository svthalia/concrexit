from typing import Any

from django.db.models import Model
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from payments.api.fields import PaymentTypeField
from payments.models import Payment
from pizzas.models import Product, PizzaEvent, Order
from pizzas.services import can_change_order


class PizzaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('pk', 'name', 'description', 'price', 'available')


class PizzaEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PizzaEvent
        fields = ('start', 'end', 'event', 'title', 'is_admin')

    event = serializers.PrimaryKeyRelatedField(read_only=True)
    is_admin = serializers.SerializerMethodField('_is_admin')

    def _is_admin(self, instance):
        member = self.context['request'].member
        return can_change_order(member, instance)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('pk', 'payment', 'product', 'name', 'member')
        read_only_fields = ('pk', 'payment', 'name', 'member')

    payment = PaymentTypeField(source='payment.type',
                               choices=Payment.PAYMENT_TYPE,
                               read_only=True)


class AdminOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('pk', 'payment', 'product', 'name', 'member')

    payment = PaymentTypeField(source='payment.type',
                               choices=Payment.PAYMENT_TYPE)

    def validate(self, attrs):
        if attrs.get('member') and attrs.get('name'):
            raise ValidationError({
                'member': _('Either specify a member or a name'),
                'name': _('Either specify a member or a name'),
            })
        if not (attrs.get('member') or attrs.get('name')) and not self.partial:
            attrs['member'] = self.context['request'].member
        return super().validate(attrs)

    def update(self, instance: Model, validated_data: Any) -> Any:
        if validated_data.get(
            'payment', {}
        ).get('type', instance.payment.type) != instance.payment.type:
            instance.payment.type = validated_data['payment']['type']
            instance.payment.save()
        if 'payment' in validated_data:
            del validated_data['payment']
        return super().update(instance, validated_data)
