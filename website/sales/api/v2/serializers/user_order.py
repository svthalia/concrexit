from sales.api.v2.admin.serializers.order import (
    OrderItemSerializer,
    OrderSerializer,
    ProductNameRelatedField,
)
from sales.models.product import ProductListItem


class UserProductNameRelatedField(ProductNameRelatedField):
    def get_queryset(self):
        shift = self.root.context.get("shift", None)
        if shift is None:
            shift = self.root.instance.shift
        return ProductListItem.objects.filter(
            product_list=shift.user_order_period.product_list
        )


class UserOrderItemSerializer(OrderItemSerializer):
    product = UserProductNameRelatedField("product")


class UserOrderSerializer(OrderSerializer):
    order_item_serializer_class = UserOrderItemSerializer
