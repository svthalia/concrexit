from django.utils.html import strip_spaces_between_tags
from rest_framework import serializers

from announcements.api.v1.serializers import SlideSerializer
from events import services
from events.api.v1.serializers.event_registrations.list import (
    EventRegistrationAdminListSerializer,
)
from events.models import Event, EventRegistration
from thaliawebsite.templatetags.bleach_tags import bleach
from utils.snippets import create_google_maps_url


class EventRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for events."""

    class Meta:
        model = Event
        fields = (
            "pk",
            "title",
            "description",
            "start",
            "end",
            "organiser",
            "category",
            "registration_start",
            "registration_end",
            "cancel_deadline",
            "location",
            "map_location",
            "price",
            "fine",
            "max_participants",
            "num_participants",
            "user_registration",
            "registration_allowed",
            "no_registration_message",
            "has_fields",
            "is_pizza_event",
            "google_maps_url",
            "is_admin",
            "slide",
            "cancel_too_late_message",
        )

    description = serializers.SerializerMethodField("_description")
    user_registration = serializers.SerializerMethodField("_user_registration")
    num_participants = serializers.SerializerMethodField("_num_participants")
    registration_allowed = serializers.SerializerMethodField("_registration_allowed")
    has_fields = serializers.SerializerMethodField("_has_fields")
    is_pizza_event = serializers.SerializerMethodField("_is_pizza_event")
    google_maps_url = serializers.SerializerMethodField("_google_maps_url")
    is_admin = serializers.SerializerMethodField("_is_admin")
    slide = SlideSerializer()

    def _description(self, instance):
        return strip_spaces_between_tags(bleach(instance.description))

    def _num_participants(self, instance):
        if (
            instance.max_participants
            and instance.participants.count() > instance.max_participants
        ):
            return instance.max_participants
        return instance.participants.count()

    def _user_registration(self, instance):
        try:
            if self.context["request"].member:
                reg = instance.eventregistration_set.get(
                    member=self.context["request"].member
                )
                return EventRegistrationAdminListSerializer(
                    reg, context=self.context
                ).data
        except EventRegistration.DoesNotExist:
            pass
        return None

    def _registration_allowed(self, instance):
        member = self.context["request"].member
        return (
            self.context["request"].user.is_authenticated
            and member.has_active_membership
            and member.can_attend_events
        )

    def _has_fields(self, instance):
        return instance.has_fields

    def _is_pizza_event(self, instance):
        return instance.has_food_event

    def _google_maps_url(self, instance):
        return create_google_maps_url(instance.map_location, zoom=13, size="450x250")

    def _is_admin(self, instance):
        member = self.context["request"].member
        return services.is_organiser(member, instance)
