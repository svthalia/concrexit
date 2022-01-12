from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from members.api.v2.serializers.member import MemberSerializer
from members.models import Member
from payments.api.v2.serializers import PaymentSerializer
from pizzas.api.v2.admin.serializers.product import ProductAdminSerializer
from pizzas.api.v2.admin.validators import MutuallyExclusiveValidator
from pizzas.api.v2.serializers import Product
from pizzas.models import FoodOrder
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class FoodOrderAdminSerializer(CleanedModelSerializer):
    class Meta:
        model = FoodOrder
        fields = ("pk", "payment", "product", "name", "member", "food_event")
        validators = [
            UniqueTogetherValidator(
                queryset=FoodOrder.objects.all(), fields=["food_event", "member"],
            ),
            MutuallyExclusiveValidator(fields=["name", "member"],),
        ]
        read_only_fields = ("payment",)

    payment = PaymentSerializer()
    product = ProductAdminSerializer()
    member = MemberSerializer(admin=True, detailed=False, required=False)

    def to_internal_value(self, data):
        self.fields["member"] = serializers.PrimaryKeyRelatedField(
            queryset=Member.objects.all(), required=False, allow_null=True
        )
        self.fields["product"] = serializers.PrimaryKeyRelatedField(
            queryset=Product.objects.all()
        )
        return super().to_internal_value(data)

    def to_representation(self, instance):
        self.fields["product"] = ProductAdminSerializer(read_only=True)
        self.fields["member"] = MemberSerializer(
            admin=True, detailed=False, read_only=True
        )
        return super().to_representation(instance)
