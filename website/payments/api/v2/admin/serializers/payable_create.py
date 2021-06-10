from rest_framework.fields import ChoiceField
from rest_framework.serializers import Serializer

from payments.models import Payment


class PayableCreateAdminSerializer(Serializer):
    """Serializer to create a payment from a payable."""

    payment_type = ChoiceField(
        choices=[Payment.TPAY, Payment.CASH, Payment.CARD, Payment.WIRE]
    )
