from payments.models import Payment
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class PaymentSerializer(CleanedModelSerializer):
    class Meta:
        model = Payment
        fields = ["pk", "type", "amount", "created_at", "topic", "notes"]
