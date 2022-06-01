from rest_framework import serializers

from payments.models import PaymentAmountField


class PaymentAmountSerializer(serializers.DecimalField):
    def __init__(self, **kwargs):
        kwargs["max_digits"] = PaymentAmountField.MAX_DIGITS
        kwargs["decimal_places"] = PaymentAmountField.DECIMAL_PLACES
        super().__init__(**kwargs)
