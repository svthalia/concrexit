from rest_framework.serializers import ModelSerializer

from members.api.v2.serializers.member import MemberSerializer
from payments.models import Payment
from thaliawebsite.api.v2.fields import CurrentMemberField


class PaymentCreateSerializer(ModelSerializer):
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

    processed_by = CurrentMemberField()


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

    paid_by = MemberSerializer(detailed=False)
    processed_by = MemberSerializer(detailed=False)
