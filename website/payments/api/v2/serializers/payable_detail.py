from rest_framework.fields import BooleanField, CharField, DecimalField
from rest_framework.serializers import Serializer

from .payment import PaymentSerializer


class PayableSerializer(Serializer):
    """Serializer to show payable information."""

    amount = DecimalField(decimal_places=2, max_digits=1000, source="payment_amount")
    topic = CharField(source="payment_topic")
    notes = CharField(source="payment_notes")
    payment = PaymentSerializer(read_only=True)
    tpay_allowed = BooleanField()
