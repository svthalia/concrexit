from html import unescape

from django.utils.html import strip_tags
from rest_framework import serializers

from announcements.api.v1.serializers import SlideSerializer
from events import services
from events.models import Event
from thaliawebsite.api.v1.cleaned_model_serializer import CleanedModelSerializer


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
            "slide",
        )

    description = serializers.SerializerMethodField("_description")
    registered = serializers.SerializerMethodField("_registered")
    pizza = serializers.SerializerMethodField("_pizza")
    present = serializers.SerializerMethodField("_present")
    slide = SlideSerializer()

    def _description(self, instance):
        return unescape(strip_tags(instance.description))

    def _registered(self, instance):
        try:
            registered = services.is_user_registered(
                self.context["request"].user, instance,
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
            present = services.is_user_present(self.context["request"].user, instance,)
            if present is None:
                return False
            return present
        except AttributeError:
            return False
