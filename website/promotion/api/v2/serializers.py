from rest_framework import serializers

from promotion.models import PromotionRequest
from thaliawebsite.api.v2.serializers import CleanedHTMLSerializer
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class PromotionRequestSerializer(CleanedModelSerializer):
    """A promotion request, as needed by the people carrying it out.

    Only the status can be changed.
    """

    class Meta:
        model = PromotionRequest
        fields = (
            "pk",
            "event",
            "event_title",
            "event_start",
            "event_url",
            "event_description",
            "publish_date",
            "channel",
            "status",
            "assigned_to",
            "drive_folder",
            "remarks",
        )
        read_only_fields = tuple(f for f in fields if f != "status")

    event_title = serializers.CharField(
        source="event.title", default=None, read_only=True
    )
    event_start = serializers.DateTimeField(
        source="event.start", default=None, read_only=True
    )
    event_url = serializers.SerializerMethodField()
    event_description = CleanedHTMLSerializer(
        source="event.description", default=None, read_only=True
    )
    channel = serializers.CharField(source="channel.name", read_only=True)
    remarks = CleanedHTMLSerializer(read_only=True)

    def get_event_url(self, instance):
        if instance.event is None:
            return None
        return self.context["request"].build_absolute_uri(
            instance.event.get_absolute_url()
        )
