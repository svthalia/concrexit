from rest_framework.fields import CharField, empty, DecimalField
from rest_framework.serializers import Serializer

from payments.api.v2.serializers import PaymentSerializer


class PayableSerializer(Serializer):
    """Serializer to show payable information."""

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        if instance:
            self.amount = instance.payment_amount
            self.topic = instance.payment_topic
            self.notes = instance.payment_notes
            self.payment = instance.payment

    amount = DecimalField(decimal_places=2, max_digits=1000)
    topic = CharField()
    notes = CharField()
    payment = PaymentSerializer(read_only=True)
