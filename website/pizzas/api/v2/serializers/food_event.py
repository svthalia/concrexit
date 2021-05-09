from rest_framework import serializers

from events.api.v2.serializers.event import EventSerializer
from pizzas.models import FoodEvent
from pizzas.services import can_change_order


class FoodEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodEvent
        fields = (
            "pk",
            "start",
            "end",
            "event",
            "title",
            "can_manage",
            "num_orders",
        )

    event = EventSerializer()
    can_manage = serializers.SerializerMethodField("_can_manage")
    num_orders = serializers.IntegerField(source="orders.count")

    def _can_manage(self, instance):
        member = self.context["request"].member
        return can_change_order(member, instance)
