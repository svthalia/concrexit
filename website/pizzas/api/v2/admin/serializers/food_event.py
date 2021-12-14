from rest_framework import serializers

from events.api.v2.serializers.event import EventSerializer
from events.models import Event
from pizzas.models import FoodEvent
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class FoodEventAdminSerializer(CleanedModelSerializer):
    class Meta:
        model = FoodEvent
        fields = (
            "pk",
            "start",
            "end",
            "event",
            "send_notification",
            "end_reminder",
            "tpay_allowed",
        )
        read_only_fields = ("end_reminder",)

    def to_internal_value(self, data):
        self.fields["event"] = serializers.PrimaryKeyRelatedField(
            queryset=Event.objects.all()
        )
        return super().to_internal_value(data)

    def to_representation(self, instance):
        self.fields["event"] = EventSerializer(read_only=True)
        return super().to_representation(instance)
