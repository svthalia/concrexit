from rest_framework import serializers


class PaymentTypeField(serializers.ChoiceField):
    NO_PAYMENT = "no_payment"

    def __init__(self, choices, **kwargs):
        choices = choices + (self.NO_PAYMENT,)
        super().__init__(choices, **kwargs)

    def get_attribute(self, instance):
        if not instance.payment:
            return self.NO_PAYMENT
        return super().get_attribute(instance)
