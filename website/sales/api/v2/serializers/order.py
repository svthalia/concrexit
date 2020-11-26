from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_str
from rest_framework import serializers

from members.api.v2.serializers.member import MemberSerializer
from payments.api.v1.serializers import PaymentSerializer
from sales.models.order import Order, OrderItem
from sales.models.product import ProductListItem


class ProductNameRelatedField(serializers.SlugRelatedField):
    def get_queryset(self):
        shift = self.root.context.get("shift", None)
        if shift is None:
            shift = self.root.instance.shift
        return ProductListItem.objects.filter(product_list=shift.product_list)

    def to_internal_value(self, data):
        if type(data) is ProductListItem:
            return data

        queryset = self.get_queryset()
        try:
            return queryset.get(product__name=data)
        except ObjectDoesNotExist:
            self.fail(
                "does_not_exist", slug_name=self.slug_field, value=smart_str(data)
            )
        except (TypeError, ValueError):
            self.fail("invalid")

    def to_representation(self, obj):
        return obj.product.name


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""

    class Meta:
        model = OrderItem
        fields = ("product", "amount", "total")
        read_only_fields = ("total",)

    product = ProductNameRelatedField("product")

    total = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=0, read_only=True
    )

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request", None)
        if request and request.user and request.user.has_perm("sales.custom_prices"):
            fields["total"].read_only = False
        return fields

    def create(self, validated_data, **kwargs):
        order = self.context["order"]
        item = OrderItem.objects.create(order=order, **validated_data)
        return item

    def update(self, instance, validated_data, **kwargs):
        order = self.context["order"]
        instance.order = order
        instance.total = None  # Always recalculate the total amount if updating using API (note the difference from the model that only recalculates if the total is None, to deal with historic data and allow for special discounts)
        super().update(instance, validated_data)
        return instance


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders."""

    class Meta:
        model = Order
        fields = (
            "pk",
            "shift",
            "created_at",
            "order_items",
            "order_description",
            "age_restricted",
            "subtotal",
            "discount",
            "total_amount",
            "num_items",
            "payment",
            "payer",
            "payment_url",
        )
        read_only_fields = (
            "pk",
            "created_at",
            "payment",
            "num_items",
            "order_description",
        )

    shift = serializers.PrimaryKeyRelatedField(read_only=True)

    age_restricted = serializers.BooleanField(read_only=True)

    order_items = OrderItemSerializer(many=True, required=False)

    subtotal = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=0, read_only=True
    )

    discount = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=0, read_only=True
    )

    total_amount = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=0, read_only=True
    )

    payment = PaymentSerializer(read_only=True)

    payer = MemberSerializer(read_only=True)

    payment_url = serializers.URLField(read_only=True)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request", None)
        if request and request.user and request.user.has_perm("sales.custom_prices"):
            try:
                fields["discount"].read_only = False
            except KeyError:
                pass
        return fields

    def create(self, validated_data):
        shift = self.context["shift"]
        order = Order.objects.create(shift=shift)
        if "order_items" in validated_data:
            items_data = validated_data.pop("order_items")
            for item_data in items_data:
                OrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        # Update the order items for an order
        if "order_items" in validated_data:
            items_data = validated_data.pop("order_items")
            current_items = list(instance.order_items.all())

            # Overwrite all existing order items by the newly provided ones
            for item_data in items_data:
                if len(current_items) > 0:
                    item = current_items.pop(0)
                    OrderItemSerializer(item, context={"order": instance}).update(
                        item, item_data
                    )
                else:
                    # Create new order items if required
                    OrderItemSerializer(context={"order": instance}).create(
                        validated_data=item_data
                    )

            # Delete all order items that we have not updated
            for i in current_items:
                i.delete()

        # Update other fields of the order as default
        instance = super().update(instance, validated_data)
        instance = Order.objects.get(
            pk=instance.pk
        )  # refresh from database to update queryable properties
        return instance


class OrderListSerializer(OrderSerializer):
    class Meta:
        model = Order
        fields = (
            "pk",
            "created_at",
            "total_amount",
            "num_items",
        )
        read_only_fields = (
            "pk",
            "created_at",
            "total_amount",
            "num_items",
        )
