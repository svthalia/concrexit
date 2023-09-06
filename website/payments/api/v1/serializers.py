from rest_framework.fields import CharField
from rest_framework.serializers import Serializer

from payments.models import Payment
from thaliawebsite.api.v1.cleaned_model_serializer import CleanedModelSerializer


class PaymentSerializer(CleanedModelSerializer):
    class Meta:
        model = Payment
        fields = ["pk", "get_type_display", "amount", "created_at", "topic", "notes"]


class PaymentCreateSerializer(Serializer):
    """Serializer for create payments data."""

    app_label = CharField()
    model_name = CharField()
    payable_pk = CharField()  # A pk can be either a UUID or an integer
