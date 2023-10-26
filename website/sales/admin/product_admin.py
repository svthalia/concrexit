from typing import Any

from django.contrib import admin
from django.contrib.admin import register
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from sales.models.product import Product, ProductList, ProductListItem


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

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        queryset = super().get_queryset(request)
        return queryset.filter(~Q(name="Merchandise Product List"))
