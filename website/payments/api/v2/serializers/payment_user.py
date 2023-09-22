from rest_framework.fields import BooleanField, DecimalField
from rest_framework.serializers import Serializer

from payments.models import PaymentUser


class PaymentUserSerializer(Serializer):
    """Serializer to show payment users."""

    class Meta:
        model = PaymentUser

    tpay_balance = DecimalField(decimal_places=2, max_digits=1000)
    tpay_allowed = BooleanField()
    tpay_enabled = BooleanField()
