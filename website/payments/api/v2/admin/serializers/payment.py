from rest_framework.fields import HiddenField

from members.api.v2.serializers.member import MemberSerializer
from payments.api.v2.serializers.payment_user import PaymentUserSerializer
from payments.models import Payment
from thaliawebsite.api.v2.fields import CurrentMemberDefault
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class PaymentCreateSerializer(CleanedModelSerializer):
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
        read_only_fields = ("created_at",)

    processed_by = HiddenField(default=CurrentMemberDefault())


class PaymentAdminSerializer(CleanedModelSerializer):
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
        read_only_fields = (
            "pk",
            "type",
            "paid_by",
            "processed_by",
            "amount",
            "created_at",
            "topic",
            "notes",
        )

    paid_by = PaymentUserSerializer(read_only=False)
    processed_by = PaymentUserSerializer(read_only=False)
