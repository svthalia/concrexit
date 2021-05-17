from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from members.api.v2.serializers.member import MemberSerializer
from payments.api.v2.serializers import PaymentSerializer
from pizzas.api.v2.serializers.product import ProductSerializer
from pizzas.models import FoodOrder
from thaliawebsite.api.v2 import fields


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
        fields = ("product", "member")
        validators = [
            UniqueTogetherValidator(
                queryset=FoodOrder.objects.all(), fields=["product", "member"],
            )
        ]

    member = fields.CurrentMemberField()


class FoodOrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOrder
        fields = ("product",)
