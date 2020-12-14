from functools import partial

from django.contrib import admin
from django.contrib.admin import register
from django.forms import Field
from django.http import HttpRequest
from django.urls import resolve

from payments.widgets import PaymentWidget
from sales.models.order import Order, OrderItem
from sales.models.product import Product, ProductList, ProductListItem
from sales.models.shift import Shift


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    fields = ("product", "amount", "total")

    def get_parent_object_from_request(self, request):
        """
        Returns the parent object from the request or None.

        Note that this only works for Inlines, because the `parent_model`
        is not available in the regular admin.ModelAdmin as an attribute.
        """
        resolved = resolve(request.path_info)
        if resolved.kwargs:
            parent = self.parent_model.objects.get(pk=resolved.kwargs['object_id'])
            return parent
        return None

    def has_add_permission(self, request, obj):
        if obj and obj.payment:
            return False

        parent = self.get_parent_object_from_request(request)
        if not parent:
            return False

        # No parent - return original has_add_permission() check
        return super(OrderItemInline, self).has_add_permission(request, obj)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):

        field = super(OrderItemInline, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )

        if db_field.name == "product":
            if request is not None:
                parent = self.get_parent_object_from_request(request)
                if parent:
                    field.queryset = self.get_parent_object_from_request(
                        request
                    ).shift.product_list.productlistitem_set
            else:
                field.queryset = field.queryset.none()

        return field

    def has_delete_permission(self, request, obj=None):
        if obj and obj.payment:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        return False


@register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [
        OrderItemInline,
    ]

    list_display = (
        "id",
        "shift",
        "created_at",
        "total_amount",
        "discount",
        "payment",
        "order_description",
        "get_member",
    )

    fields = (
        "shift",
        "created_at",
        "total_amount",
        "discount",
        "payment",
        "order_description",
        "age_restricted",
    )

    readonly_fields = (
        "created_at",
        "total_amount",
        "order_description",
        "age_restricted",
    )

    def get_member(self, obj):
        return obj.payment.paid_by if obj and obj.payment else None

    get_member.short_description = "member"

    def get_readonly_fields(self, request: HttpRequest, obj: Order = None):
        default_fields = self.readonly_fields

        if obj and obj.shift:
            default_fields += ("shift", )

        if obj and obj.payment:
            return self.fields

        return default_fields

    def age_restricted(self, obj):
        return obj.age_restricted if obj else None

    age_restricted.boolean = True

    def get_form(self, request, obj=None, **kwargs):
        return super().get_form(
            request,
            obj,
            formfield_callback=partial(
                self.formfield_for_dbfield, request=request, obj=obj
            ),
            **kwargs
        )

    def formfield_for_dbfield(self, db_field, request, obj=None, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "payment":
            return Field(
                widget=PaymentWidget(obj=obj), initial=field.initial, required=False
            )
        return field


@register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "age_restricted"
    )


class ProductListItemInline(admin.TabularInline):
    model = ProductListItem
    extra = 0


@register(ProductList)
class ProductListAdmin(admin.ModelAdmin):
    inlines = [
        ProductListItemInline,
    ]


class OrderInline(admin.TabularInline):
    model = Order
    extra = 0
    show_change_link = True
    can_delete = False

    fields = (
        "created_at",
        "id",
        "order_description",
        "discount",
        "total_amount",
        "payment",
    )

    readonly_fields = (
        "created_at",
        "id",
        "order_description",
        "discount",
        "total_amount",
        "payment",
    )

    def has_add_permission(self, request, obj):
        return False


@register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    inlines = [
        OrderInline,
    ]
    list_display = (
        "id",
        "start_date",
        "end_date",
        "product_list",
        "total_revenue",
    )

    fields = (
        "start_date",
        "end_date",
        "product_list",
        "total_revenue",
    )

    readonly_fields = ("total_revenue",)
