from rest_framework import serializers

from payments.models import Payment


class PaymentTypeField(serializers.ChoiceField):
    def get_attribute(self, instance):
        if not instance.payment:
            return Payment.NONE
        return super().get_attribute(instance)
