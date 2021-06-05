from rest_framework import serializers

from events.models import EventRegistration
from members.api.v2.serializers.member import MemberSerializer
from members.models import Member


class EventRegistrationSerializer(serializers.ModelSerializer):
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
        )
        read_only_fields = ("payment",)

    def to_internal_value(self, data):
        self.fields["member"] = serializers.PrimaryKeyRelatedField(
            queryset=Member.objects.all()
        )
        return super().to_internal_value(data)

    def to_representation(self, instance):
        self.fields["member"] = MemberSerializer(detailed=False, read_only=True)
        return super().to_representation(instance)
