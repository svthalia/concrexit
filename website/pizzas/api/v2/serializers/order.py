from rest_framework import fields, serializers
from rest_framework.validators import UniqueTogetherValidator

from members.api.v2.serializers.member import MemberSerializer
from payments.api.v2.serializers import PaymentSerializer
from pizzas.api.v2.serializers.product import ProductSerializer
from pizzas.models import FoodEvent, FoodOrder
from thaliawebsite.api.v2.fields import (
    CurrentMemberDefault,
    CurrentRequestObjectDefault,
)


class FoodOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOrder
        fields = ("pk", "payment", "product", "name", "member")
        read_only_fields = ("pk", "payment", "name", "member")

    product = ProductSerializer()
    payment = PaymentSerializer()
    member = MemberSerializer(detailed=False)


class FoodOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOrder
        fields = ("product", "member", "food_event")
        validators = [
            UniqueTogetherValidator(
                queryset=FoodOrder.objects.all(),
                fields=["food_event", "member"],
            )
        ]

    food_event = fields.HiddenField(
        default=CurrentRequestObjectDefault(FoodEvent, url_field="pk")
    )
    member = fields.HiddenField(default=CurrentMemberDefault())


class FoodOrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOrder
        fields = ("product",)
