from rest_framework.serializers import ModelSerializer

from payments.models import Payment


class PaymentSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = ["pk", "type", "amount", "created_at", "topic", "notes"]
