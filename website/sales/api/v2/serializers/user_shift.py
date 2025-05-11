from rest_framework import serializers

from sales.api.v2.admin.serializers.shift import ProductListItemSerializer
from sales.models.shift import Shift


class UserShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = (
            "pk",
            "title",
            "start",
            "end",
            "products",
        )

    products = ProductListItemSerializer(
        source="product_list.product_items", many=True, read_only=True
    )
