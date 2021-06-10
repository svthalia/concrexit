from rest_framework.fields import HiddenField
from rest_framework.serializers import ModelSerializer

from members.api.v2.serializers.member import MemberSerializer
from payments.models import Payment
from thaliawebsite.api.v2.fields import CurrentMemberDefault


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

    processed_by = HiddenField(default=CurrentMemberDefault())


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

    paid_by = MemberSerializer(detailed=False, read_only=False)
    processed_by = MemberSerializer(detailed=False, read_only=False)
