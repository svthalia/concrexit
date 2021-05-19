from rest_framework.fields import CharField, empty, ListField, DecimalField
from rest_framework.serializers import Serializer

from members.api.v2.serializers.member import MemberSerializer
from payments.api.v2.admin.serializers.payment import PaymentSerializer
from payments.models import Payment
from payments.payables import Payable


class PayableDetailSerializer(Serializer):
    """Serializer to show payable information."""

    def __init__(self, payable: Payable = None, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.payable = payable

    def get_initial(self):
        initial_data = {
            "allowed_payment_types": [Payment.CASH, Payment.CARD, Payment.WIRE],
        }

        if self.payable:
            if self.payable.tpay_allowed:
                initial_data["allowed_payment_types"].append(Payment.TPAY)
            initial_data["payment"] = PaymentSerializer().to_representation(self.payable.payment) if self.payable.payment else None
            initial_data["amount"] = self.payable.payment_amount
            initial_data["payer"] = MemberSerializer(context=self.context, detailed=False).to_representation(self.payable.payment_payer)
            initial_data["topic"] = self.payable.payment_topic
            initial_data["notes"] = self.payable.payment_notes
        return initial_data

    allowed_payment_types = ListField(child=CharField())
    amount = DecimalField(decimal_places=2, max_digits=1000)
    payer = MemberSerializer(detailed=False)
    topic = CharField()
    notes = CharField()
    payment = CharField()
