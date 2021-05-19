from rest_framework.serializers import ModelSerializer

from payments.models import Payment


class PaymentSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "pk",
            "type",
            "paid_by",
            "processed_by",
            "amount",
            "created_at",
            "topic",
            "notes",
        )
