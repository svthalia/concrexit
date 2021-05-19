from rest_framework.fields import CharField, empty, ListField, DecimalField
from rest_framework.serializers import Serializer

from members.api.v2.serializers.member import MemberSerializer
from payments.api.v2.serializers import PaymentSerializer
from payments.models import Payment
from payments.payables import Payable


class PayableSerializer(Serializer):
    """Serializer to show payable information."""

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.allowed_payment_types = [Payment.CASH, Payment.CARD, Payment.WIRE]
        if instance:
            self.amount = instance.payment_amount
            self.topic = instance.payment_topic
            self.notes = instance.payment_notes
            self.payment = instance.payment

    amount = DecimalField(decimal_places=2, max_digits=1000)
    topic = CharField()
    notes = CharField()
    payment = CharField()
