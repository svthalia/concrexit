from rest_framework import serializers

from events.api.v2.serializers.event import EventSerializer
from pizzas.api.v2.serializers.order import FoodOrderSerializer
from pizzas.models import FoodEvent, FoodOrder
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
            "order",
        )

    event = EventSerializer()
    can_manage = serializers.SerializerMethodField("_can_manage")
    order = serializers.SerializerMethodField("_member_order")

    def _member_order(self, instance):
        try:
            order = instance.orders.get(member=self.context["request"].member)
            return FoodOrderSerializer(order, context=self.context,).data
        except FoodOrder.DoesNotExist:
            pass
        return None

    def _can_manage(self, instance):
        member = self.context["request"].member
        return can_change_order(member, instance)
