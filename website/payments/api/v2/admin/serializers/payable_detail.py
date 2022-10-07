from rest_framework.fields import CharField, DecimalField, ListField
from rest_framework.serializers import Serializer

from members.api.v2.serializers.member import MemberSerializer
from payments.api.v2.admin.serializers.payment import PaymentAdminSerializer
from payments.models import Payment


class PayableAdminSerializer(Serializer):
    """Serializer to show payable information."""

    allowed_payment_types = ListField(
        child=CharField(),
        default=[
            Payment.CASH,
            Payment.CARD,
            Payment.WIRE,
        ],
    )
    amount = DecimalField(decimal_places=2, max_digits=1000, source="payment_amount")
    payer = MemberSerializer(
        admin=True, detailed=False, read_only=True, source="payment_payer"
    )
    topic = CharField(source="payment_topic")
    notes = CharField(source="payment_notes")
    payment = PaymentAdminSerializer(read_only=True)
