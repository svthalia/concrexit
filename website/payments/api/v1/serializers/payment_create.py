from rest_framework.fields import CharField
from rest_framework.serializers import Serializer


class PaymentCreateSerializer(Serializer):
    """Serializer for create payments data."""

    app_label = CharField()
    model_name = CharField()
    payable_pk = CharField()  # A pk can be either a UUID or an integer
