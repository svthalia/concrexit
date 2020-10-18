from html import unescape

from django.utils.html import strip_tags
from rest_framework import serializers

from events import services
from events.models import Event
from pizzas.models import PizzaEvent


class EventListSerializer(serializers.ModelSerializer):
    """Custom list serializer for events"""

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
                self.context["request"].user, instance,
            )
            if registered is None:
                return False
            return registered
        except AttributeError:
            return False

    def _pizza(self, instance):
        pizza_events = PizzaEvent.objects.filter(event=instance)
        return pizza_events.exists()

    def _present(self, instance):
        try:
            present = services.is_user_present(self.context["request"].user, instance,)
            if present is None:
                return False
            return present
        except AttributeError:
            return False
