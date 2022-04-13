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

    title = serializers.SerializerMethodField("_get_title")

    def _get_title(self, instance):
        return instance.title

    start = serializers.DateTimeField(source="user_order_period.start", read_only=True)

    end = serializers.DateTimeField(source="user_order_period.end", read_only=True)

    products = ProductListItemSerializer(
        source="user_order_period.product_list.product_items", many=True, read_only=True
    )
