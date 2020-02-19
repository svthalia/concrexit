from rest_framework import serializers

from payments.models import Payment


class PaymentTypeField(serializers.ChoiceField):
    def __init__(self, choices, **kwargs):
        super().__init__(choices, **kwargs)

    def get_attribute(self, instance):
        if not instance.payment:
            return Payment.NONE
        return super().get_attribute(instance)

    def to_representation(self, value):
        return super().to_representation(value).value


