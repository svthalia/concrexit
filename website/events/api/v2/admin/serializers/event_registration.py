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
            "queue_position",
            "is_cancelled",
            "is_late_cancellation",
        )
        read_only_fields = ("payment",)
        optional_fields = ["payment", "member", "name", "special_prize", "remarks"]

    payment = PaymentSerializer(required=False)
    is_cancelled = serializers.SerializerMethodField("_is_cancelled")
    is_late_cancellation = serializers.SerializerMethodField("_is_late_cancellation")
    queue_position = serializers.SerializerMethodField("_queue_position")

    def create(self, validated_data):
        event = self.context["event"]
        validated_data.update({"event": event})
        return super().create(validated_data)

    def _is_late_cancellation(self, instance):
        return instance.is_late_cancellation()

    def _queue_position(self, instance):
        pos = instance.queue_position
        return pos if pos and pos > 0 else None

    def _is_cancelled(self, instance):
        return instance.date_cancelled is not None

    def to_internal_value(self, data):
        self.fields["member"] = serializers.PrimaryKeyRelatedField(
            queryset=Member.objects.all(), required=False
        )
        return super().to_internal_value(data)

    def to_representation(self, instance):
        self.fields["member"] = MemberSerializer(
            admin=True, detailed=False, read_only=True
        )
        return super().to_representation(instance)
