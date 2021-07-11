from rest_framework import serializers

from events.models import EventRegistration
from members.api.v2.serializers.member import MemberSerializer
from payments.api.v2.serializers import PaymentSerializer


class EventRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for event registrations."""

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", {"pk", "member", "name"})

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        allowed = set(fields)
        existing = set(self.fields.keys())
        for field_name in existing - allowed:
            self.fields.pop(field_name)

    class Meta:
        model = EventRegistration
        fields = (
            "pk",
            "present",
            "queue_position",
            "date",
            "payment",
            "member",
            "name",
        )

    payment = PaymentSerializer()
    member = MemberSerializer(detailed=False, read_only=True)
