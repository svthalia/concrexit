from rest_framework import serializers

from activemembers.api.v2.serializers.member_group import MemberGroupSerializer
from announcements.api.v2.serializers import SlideSerializer
from documents.api.v2.serializers.document import DocumentSerializer
from events import services
from events.api.v2.serializers.event_registration import EventRegistrationSerializer
from events.models import Event, EventRegistration
from thaliawebsite.api.v2.serializers import CleanedHTMLSerializer
from utils.snippets import create_google_maps_url


class EventSerializer(serializers.ModelSerializer):
    """Serializer for events."""

    class Meta:
        model = Event
        fields = (
            "pk",
            "title",
            "description",
            "start",
            "end",
            "category",
            "registration_start",
            "registration_end",
            "cancel_deadline",
            "optional_registrations",
            "location",
            "price",
            "fine",
            "num_participants",
            "max_participants",
            "no_registration_message",
            "cancel_too_late_message",
            "has_fields",
            "food_event",
            "maps_url",
            "user_permissions",
            "user_registration",
            "organiser",
            "slide",
            "documents",
        )

    description = CleanedHTMLSerializer()
    organiser = MemberGroupSerializer()
    user_registration = serializers.SerializerMethodField("_user_registration")
    num_participants = serializers.SerializerMethodField("_num_participants")
    maps_url = serializers.SerializerMethodField("_maps_url")
    price = serializers.DecimalField(max_digits=5, decimal_places=2)
    fine = serializers.DecimalField(max_digits=5, decimal_places=2)
    slide = SlideSerializer()
    documents = DocumentSerializer(many=True)
    user_permissions = serializers.SerializerMethodField("_user_permissions")

    def _user_registration(self, instance):
        try:
            if self.context["request"].member:
                reg = instance.eventregistration_set.get(
                    member=self.context["request"].member
                )
                return EventRegistrationSerializer(
                    reg,
                    context=self.context,
                    fields=(
                        "pk",
                        "present",
                        "queue_position",
                        "is_cancelled",
                        "is_late_cancellation",
                        "date",
                        "payment",
                    ),
                ).data
        except EventRegistration.DoesNotExist:
            pass
        return None

    def _num_participants(self, instance):
        if (
            instance.max_participants
            and instance.participants.count() > instance.max_participants
        ):
            return instance.max_participants
        return instance.participants.count()

    def _user_permissions(self, instance):
        member = self.context["request"].member
        return services.event_permissions(member, instance)

    def _maps_url(self, instance):
        return create_google_maps_url(instance.map_location, zoom=13, size="450x250")
