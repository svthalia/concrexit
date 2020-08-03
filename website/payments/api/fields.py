from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class PaymentTypeField(serializers.ChoiceField):
    NO_PAYMENT = "no_payment"

    def __init__(self, choices, **kwargs):
        choices = choices + (self.NO_PAYMENT, _("No payment"))
        super().__init__(choices, **kwargs)

    def get_attribute(self, instance):
        if not instance.payment:
            return self.NO_PAYMENT
        return super().get_attribute(instance)
