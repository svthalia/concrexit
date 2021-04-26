from django.contrib import admin
from django.contrib.admin import register

from sales.models.product import Product, ProductListItem, ProductList


@register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "age_restricted")


class ProductListItemInline(admin.TabularInline):
    model = ProductListItem
    extra = 0


@register(ProductList)
class ProductListAdmin(admin.ModelAdmin):
    inlines = [
        ProductListItemInline,
    ]
