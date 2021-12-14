from payments.models import Payment
from thaliawebsite.api.v1.cleaned_model_serializer import CleanedModelSerializer


class PaymentSerializer(CleanedModelSerializer):
    class Meta:
        model = Payment
        fields = ["pk", "get_type_display", "amount", "created_at", "topic", "notes"]
