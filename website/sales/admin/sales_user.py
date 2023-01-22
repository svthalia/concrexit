from django.contrib import admin
from django.contrib.admin import register

from sales import services
from sales.models.order import Order
from sales.models.sales_user import SalesUser


class SalesUserOrderInline(admin.TabularInline):
    model = Order

    def has_change_permission(self, request, obj=None):
        return False


@register(SalesUser)
class SalesUserAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = (
        "__str__",
        "is_adult",
    )

    fields = (
        "__str__",
        "is_adult",
    )

    readonly_fields = ("is_adult",)

    def is_adult(self, obj):
        return services.is_adult(obj)

    is_adult.boolean = True

    inlines = [SalesUserOrderInline]
