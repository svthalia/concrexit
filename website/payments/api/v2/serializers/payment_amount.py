from rest_framework import serializers

from payments.models import PaymentAmountField


class PaymentAmountSerializer(serializers.DecimalField):
    def __init__(self, **kwargs):
        kwargs["max_digits"] = 8
        kwargs["decimal_places"] = 2
        super().__init__(**kwargs)
