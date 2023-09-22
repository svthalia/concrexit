from rest_framework import serializers
from rest_framework.reverse import reverse

from activemembers.api.v2.serializers.member_group import (
    MemberGroupSerializer,
    MemberGroupShortSerializer,
)
from documents.api.v2.serializers.document import DocumentSerializer
from events import services
from events.api.v2.serializers.event_registration import EventRegistrationSerializer
from events.models import Event
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
            "slug",
            "url",
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
            "registration_status",
            "cancel_too_late_message",
            "has_fields",
            "food_event",
            "maps_url",
            "user_permissions",
            "user_registration",
            "organisers",
            "documents",
        )

    description = CleanedHTMLSerializer()
    organisers = MemberGroupSerializer(many=True)
    user_registration = serializers.SerializerMethodField("_user_registration")
    num_participants = serializers.SerializerMethodField("_num_participants")
    maps_url = serializers.SerializerMethodField("_maps_url")
    registration_status = serializers.SerializerMethodField("_registration_status")
    price = PaymentAmountSerializer()
    fine = PaymentAmountSerializer()
    documents = DocumentSerializer(many=True)
    user_permissions = serializers.SerializerMethodField("_user_permissions")
    url = serializers.SerializerMethodField("_url")

    def _user_registration(self, instance: Event):
        if self.context["request"].member and len(instance.member_registration) > 0:
            registration = instance.member_registration[-1]
            return EventRegistrationSerializer(
                registration,
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
        return None

    def _registration_status(self, instance: Event):
        if self.context["request"].member and len(instance.member_registration) > 0:
            registration = instance.member_registration[-1]
        else:
            registration = None
        status = services.registration_status(
            instance, registration, self.context["request"].member
        )
        cancel_status = services.cancel_status(instance, registration)

        status_str = services.registration_status_string(status, instance, registration)
        cancel_str = services.cancel_info_string(instance, cancel_status, status)
        if services.show_cancel_status(status) and cancel_str != "":
            return f"{status_str} {cancel_str}"
        return f"{status_str}"

    def _num_participants(self, instance: Event):
        if instance.max_participants:
            return min(instance.participant_count, instance.max_participants)
        return instance.participant_count

    def _user_permissions(self, instance):
        member = self.context["request"].member
        return services.event_permissions(member, instance, registration_prefetch=True)

    def _url(self, instance: Event):
        if instance.slug is None:
            return reverse(
                "events:event",
                kwargs={"pk": instance.pk},
                request=self.context["request"],
            )
        return reverse(
            "events:event",
            kwargs={"slug": instance.slug},
            request=self.context["request"],
        )

    def _maps_url(self, instance):
        return self.context["request"].build_absolute_uri(
            create_google_maps_url(instance.map_location, zoom=13, size="450x250")
        )


class EventListSerializer(EventSerializer):
    organisers = MemberGroupShortSerializer(many=True)
