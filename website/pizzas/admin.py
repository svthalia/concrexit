"""Registers admin interfaces for the pizzas module."""
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.urls import reverse, path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from events import services
from events.services import is_organiser
from pizzas import admin_views
from utils.admin import DoNextModelAdmin
from .models import FoodOrder, FoodEvent, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Manage the products."""

    list_display = ("name", "price", "available")
    list_filter = ("available", "restricted")
    search_fields = ("name",)


@admin.register(FoodEvent)
class FoodEventAdmin(admin.ModelAdmin):
    """Manage the pizza events."""

    list_display = ("title", "start", "end", "notification_enabled", "orders")
    date_hierarchy = "start"
    exclude = ("end_reminder",)
    search_fields = [f"event__title_{l[0]}" for l in settings.LANGUAGES]
    autocomplete_fields = ("event",)

    def notification_enabled(self, obj):
        return obj.send_notification

    notification_enabled.short_description = _("reminder")
    notification_enabled.admin_order_field = "send_notification"
    notification_enabled.boolean = True

    def has_change_permission(self, request, obj=None):
        """Only allow access to the change form if the user is an organiser."""
        if obj is not None and not services.is_organiser(request.member, obj.event):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Only allow access to delete if the user is an organiser."""
        if obj is not None and not services.is_organiser(request.member, obj.event):
            return False
        return super().has_delete_permission(request, obj)

    def orders(self, obj):
        url = reverse("admin:pizzas_foodevent_details", kwargs={"pk": obj.pk})
        return format_html('<a href="{url}">{text}</a>', url=url, text=_("Orders"))

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/details/",
                self.admin_site.admin_view(
                    admin_views.PizzaOrderDetails.as_view(admin=self)
                ),
                name="pizzas_foodevent_details",
            ),
            path(
                "<int:pk>/overview/",
                self.admin_site.admin_view(
                    admin_views.PizzaOrderSummary.as_view(admin=self)
                ),
                name="pizzas_foodevent_overview",
            ),
        ]
        return custom_urls + urls


@admin.register(FoodOrder)
class FoodOrderAdmin(DoNextModelAdmin):
    """Manage the orders."""

    list_display = (
        "food_event",
        "member_first_name",
        "member_last_name",
        "product",
        "payment",
    )
    exclude = ("payment",)

    def save_model(self, request, obj, form, change):
        """You can only save the orders if you have permission."""
        if not is_organiser(request.member, obj.food_event.event):
            raise PermissionDenied
        return super().save_model(request, obj, form, change)

    def has_view_permission(self, request, order=None):
        """Only give view permission if the user is an organiser."""
        if order is not None and not is_organiser(
            request.member, order.food_event.event
        ):
            return False
        return super().has_view_permission(request, order)

    def has_change_permission(self, request, order=None):
        """Only give change permission if the user is an organiser."""
        if order is not None and not is_organiser(
            request.member, order.food_event.event
        ):
            return False
        return super().has_change_permission(request, order)

    def has_delete_permission(self, request, order=None):
        """Only give delete permission if the user is an organiser."""
        if order is not None and not is_organiser(
            request.member, order.food_event.event
        ):
            return False
        return super().has_delete_permission(request, order)
