from rest_framework import serializers

from events.models import EventRegistration
from members.api.v2.serializers.member import MemberSerializer
from members.models import Member
from payments.api.v2.serializers import PaymentSerializer
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class EventRegistrationAdminSerializer(CleanedModelSerializer):
    """Serializer for event registrations."""

    class Meta:
        model = EventRegistration
        fields = (
            "pk",
            "present",
            "queue_position",
            "date",
            "date_cancelled",
            "payment",
            "member",
            "name",
            "special_price",
            "remarks",
        )
        read_only_fields = ("payment",)

    payment = PaymentSerializer()

    def to_internal_value(self, data):
        self.fields["member"] = serializers.PrimaryKeyRelatedField(
            queryset=Member.objects.all()
        )
        return super().to_internal_value(data)

    def to_representation(self, instance):
        self.fields["member"] = MemberSerializer(
            admin=True, detailed=False, read_only=True
        )
        return super().to_representation(instance)
