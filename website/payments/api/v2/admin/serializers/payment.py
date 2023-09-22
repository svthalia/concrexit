from rest_framework.fields import HiddenField

from payments.api.v2.serializers.payment_user import PaymentUserSerializer
from payments.models import Payment, PaymentUser
from thaliawebsite.api.v2.fields import CurrentMemberDefault
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class MemberAsPaymentUserSerializer(PaymentUserSerializer):
    """Serializer that renders a Member as if it is a PaymentUser."""

    def to_representation(self, instance):
        if isinstance(instance, PaymentUser):
            return super().to_representation(instance)
        return super().to_representation(PaymentUser.objects.get(id=instance.id))


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

    paid_by = MemberAsPaymentUserSerializer(read_only=False)
    processed_by = MemberAsPaymentUserSerializer(read_only=False)
