from rest_framework import serializers

from activemembers.api.v2.serializers.member_group import MemberGroupSerializer
from announcements.api.v2.serializers import SlideSerializer
from documents.api.v2.serializers.document import DocumentSerializer
from events import services
from events.api.v2.serializers.event_registration import EventRegistrationSerializer
from events.models import Event, EventRegistration
from payments.api.v2.serializers.payment_amount import PaymentAmountSerializer
from thaliawebsite.api.v2.serializers import CleanedHTMLSerializer
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)
from utils.snippets import create_google_maps_url


class EventSerializer(CleanedModelSerializer):
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
    price = PaymentAmountSerializer()
    fine = PaymentAmountSerializer()
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
        participant_count = instance.participants.count()
        if instance.max_participants and participant_count > instance.max_participants:
            return instance.max_participants
        return participant_count

    def _user_permissions(self, instance):
        member = self.context["request"].member
        return services.event_permissions(member, instance)

    def _maps_url(self, instance):
        return create_google_maps_url(instance.map_location, zoom=13, size="450x250")
