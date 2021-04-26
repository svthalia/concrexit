from rest_framework import serializers

from sales.models.product import ProductListItem
from sales.models.shift import Shift


class ProductListItemSerializer(serializers.ModelSerializer):
    """Serializer for product list items."""

    class Meta:
        model = ProductListItem
        fields = ("name", "price", "age_restricted")
        read_only_fields = ("name", "price", "age_restricted")

    name = serializers.SerializerMethodField("_name")
    age_restricted = serializers.SerializerMethodField("_age_restricted")

    def _name(self, instance):
        return instance.product.name

    def _age_restricted(self, instance):
        return instance.product.age_restricted


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for shifts."""

    class Meta:
        model = Shift
        fields = (
            "pk",
            "title",
            "locked",
            "active",
            "start",
            "end",
            "products",
            "total_revenue",
            "num_orders",
            "product_sales",
        )

    total_revenue = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, read_only=True
    )

    products = ProductListItemSerializer(
        source="product_list.product_items", many=True, read_only=True
    )

    title = serializers.SerializerMethodField("_get_title")

    def _get_title(self, instance):
        return instance.title

    product_sales = serializers.JSONField()
