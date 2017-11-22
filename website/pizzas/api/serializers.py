from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from pizzas.models import Product, PizzaEvent, Order


class PizzaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('pk', 'name', 'description', 'price', 'available')


class PizzaEventSerializer(serializers.ModelSerializer):

    event = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = PizzaEvent
        fields = ('start', 'end', 'event', 'title')


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('pk', 'paid', 'product', 'name', 'member')
        read_only_fields = ('pk', 'paid', 'name', 'member')


class AdminOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('pk', 'paid', 'product', 'name', 'member')

    def validate(self, attrs):
        if attrs['member'] and attrs['name']:
            raise ValidationError({
                'member': _('Either specify a member or a name'),
                'name': _('Either specify a member or a name'),
            })
        if not (attrs['member'] or attrs['name']):
            attrs['member'] = self.context['request'].member
        return super().validate(attrs)
