"""Registers admin interfaces for the models defined in this module."""

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.shortcuts import redirect
from django.urls import reverse

from sales.admin import ProductAdmin, ProductListAdmin, ProductListItemInline
from sales.models.product import Product, ProductList

from .models import MerchandiseItem, MerchandiseProduct


class MerchandiseProductInline(admin.TabularInline):
    """Inline admin interface for the merchandise products."""

    model = MerchandiseProduct
    extra = 0

    fields = (
        "name",
        "stock_value",
    )


@admin.register(MerchandiseItem)
class MerchandiseItemAdmin(ModelAdmin):
    """This manages the admin interface for the model items."""

    #: Included fields in the admin interface
    fields = (
        "name",
        "price",
        "description",
        "image",
    )
    search_fields = ("name", "description")
    list_display = ("name", "price")
    list_filter = ("name", "price")

    inlines = [MerchandiseProductInline]


class MerchandiseDisabledProductAdmin(ProductAdmin):
    def has_change_permission(self, request, obj=None):
        if obj is not None and isinstance(obj.merchandiseproduct, MerchandiseProduct):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and isinstance(obj.merchandiseproduct, MerchandiseProduct):
            return False
        return super().has_change_permission(request, obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, object_id)
        if obj is not None and isinstance(obj.merchandiseproduct, MerchandiseProduct):
            return redirect(
                reverse(
                    "admin:merchandise_merchandiseitem_change",
                    args=(obj.merchandiseproduct.merchandise_item.id,),
                )
            )
        return super().change_view(request, object_id, form_url, extra_context)


admin.site.unregister(Product)
admin.site.register(Product, MerchandiseDisabledProductAdmin)


class MerchandiseDisabledProductListItemInline(ProductListItemInline):
    fields = (
        "product",
        "price",
        "priority",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return False

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        return readonly_fields + (
            "product",
            "price",
        )


class MerchandiseDisabledProductListAdmin(ProductListAdmin):
    inlines = [
        MerchandiseDisabledProductListItemInline,
    ]

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj is not None and obj.name == "Merchandise":
            return readonly_fields + ("name",)
        return readonly_fields

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.name == "Merchandise":
            return False
        return super().has_change_permission(request, obj)


admin.site.unregister(ProductList)
admin.site.register(ProductList, MerchandiseDisabledProductListAdmin)
