from rest_framework.fields import CharField, ListField, DecimalField, empty
from rest_framework.serializers import Serializer

from members.api.v2.serializers.member import MemberSerializer
from payments.api.v2.admin.serializers.payment import PaymentSerializer
from payments.models import Payment, PaymentUser


class PayableSerializer(Serializer):
    """Serializer to show payable information."""

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.fields['allowed_payment_types'].default = [Payment.CASH, Payment.CARD, Payment.WIRE]
        if (
            instance
            and instance.tpay_allowed
            and instance.payment_payer
            and PaymentUser.objects.get(pk=instance.payment_payer.pk).tpay_allowed
        ):
            self.fields['allowed_payment_types'].default.append(Payment.TPAY)

    allowed_payment_types = ListField(
        child=CharField()
    )
    amount = DecimalField(decimal_places=2, max_digits=1000, source="payment_amount")
    payer = MemberSerializer(detailed=False, read_only=True, source="payment_payer")
    topic = CharField(source="payment_topic")
    notes = CharField(source="payment_notes")
    payment = PaymentSerializer(read_only=True)
