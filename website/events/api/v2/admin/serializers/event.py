from rest_framework import serializers

from activemembers.api.v2.serializers.member_group import MemberGroupSerializer
from announcements.api.v2.serializers import SlideSerializer
from documents.api.v2.serializers.document import DocumentSerializer
from events import services
from events.api.v2.serializers.event_registration import EventRegistrationSerializer
from events.models import Event, EventRegistration
from thaliawebsite.api.v2.serializers.html import CleanedHTMLSerializer
from utils.snippets import create_google_maps_url


class EventSerializer(serializers.ModelSerializer):
    """Serializer for events."""

    class Meta:
        model = Event
        fields = "__all__"

    description = CleanedHTMLSerializer()
    organiser = MemberGroupSerializer()
    price = serializers.FloatField()
    fine = serializers.FloatField()
    slide = SlideSerializer()
    documents = DocumentSerializer(many=True)


class EventListSerializer(serializers.ModelSerializer):
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
            "location",
            "price",
            "fine",
            "max_participants",
            "no_registration_message",
            "has_fields",
            "organiser",
            "slide",
        )

    description = CleanedHTMLSerializer()
    organiser = MemberGroupSerializer()
    price = serializers.FloatField()
    fine = serializers.FloatField()
