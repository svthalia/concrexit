from html import unescape

from django.utils.html import strip_spaces_between_tags, strip_tags

from rest_framework import serializers

from events import services
from events.models import Event, EventRegistration
from thaliawebsite.api.v1.cleaned_model_serializer import CleanedModelSerializer
from thaliawebsite.templatetags.bleach_tags import bleach
from utils.snippets import create_google_maps_url

from .event_registrations import EventRegistrationAdminListSerializer


class EventRetrieveSerializer(CleanedModelSerializer):
    """Serializer for events."""

    class Meta:
        model = Event
        fields = (
            "pk",
            "title",
            "description",
            "caption",
            "start",
            "end",
            "organisers",
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

    def _description(self, instance):
        return strip_spaces_between_tags(bleach(instance.description))

    def _num_participants(self, instance):
        participant_count = instance.participants.count()
        if instance.max_participants and participant_count > instance.max_participants:
            return instance.max_participants
        return participant_count

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
        return self.context["request"].build_absolute_uri(
            create_google_maps_url(instance.map_location, zoom=13, size="450x250")
        )

    def _is_admin(self, instance):
        member = self.context["request"].member
        return services.is_organiser(member, instance)


class EventListSerializer(CleanedModelSerializer):
    """Custom list serializer for events."""

    class Meta:
        model = Event
        fields = (
            "pk",
            "title",
            "description",
            "start",
            "end",
            "location",
            "price",
            "registered",
            "present",
            "pizza",
            "registration_allowed",
        )

    description = serializers.SerializerMethodField("_description")
    registered = serializers.SerializerMethodField("_registered")
    pizza = serializers.SerializerMethodField("_pizza")
    present = serializers.SerializerMethodField("_present")

    def _description(self, instance):
        return unescape(strip_tags(instance.description))

    def _registered(self, instance):
        try:
            registered = services.is_user_registered(
                self.context["request"].user,
                instance,
            )
            if registered is None:
                return False
            return registered
        except AttributeError:
            return False

    def _pizza(self, instance):
        return instance.has_food_event

    def _present(self, instance):
        try:
            present = services.is_user_present(
                self.context["request"].user,
                instance,
            )
            if present is None:
                return False
            return present
        except AttributeError:
            return False
