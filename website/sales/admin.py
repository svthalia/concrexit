from django.contrib import admin
from django.contrib.admin import register
from django.forms import Field

from payments.widgets import PaymentWidget
from sales.models.order import Order, OrderItem
from sales.models.product import Product
from sales.models.product_list import ProductList, ProductListItem
from sales.models.shift import Shift


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    fields = [
        "product",
        "amount",
        "total_price"
    ]

    readonly_fields = [
        "total_price",
    ]

@register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline,]

    list_display = [
        "id",
        "shift",
        "payment_notes",
        "payment"
    ]

    fields = [
        "shift",
        "created_at",
        "total_amount",
        "discount",
        "payment",
        "payment_notes"
    ]

    readonly_fields = [
        "created_at",
        "shift",
        "total_amount",
        "payment_notes"
    ]

    def formfield_for_dbfield(self, db_field, request, obj=None, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "payment":
            return Field(
                widget=PaymentWidget(obj=obj), initial=field.initial, required=False
            )
        return field


@register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass

class ProductListItemInline(admin.TabularInline):
    model = ProductListItem
    extra = 0

@register(ProductList)
class ProductListAdmin(admin.ModelAdmin):
    inlines = [ProductListItemInline, ]


@register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    pass
