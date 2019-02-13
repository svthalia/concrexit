from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from pizzas import services
from .models import Order, PizzaEvent, Product
from events.models import Event


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available')
    list_filter = ('available', 'restricted')


@admin.register(PizzaEvent)
class PizzaEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'orders')
    exclude = ('end_reminder',)

    def orders(self, obj):
        return format_html(_('<strong><a href="{link}">Orders</a></strong>'),
                           link=reverse('pizzas:orders',
                                        kwargs={'event_pk': obj.pk}))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "event":
            kwargs["queryset"] = Event.objects.filter(
                end__gte=timezone.now())
        return super(PizzaEventAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('pizza_event', 'member_name', 'product', 'paid')

    def save_model(self, request, obj, form, change):
        if not services.is_organiser(request.member, obj.pizza_event):
            raise PermissionDenied
        return super().save_model(request, obj, form, change)

    def has_view_permission(self, request, order=None):
        """Only give view permission if the user is an organiser"""
        if (order is not None and
                not services.is_organiser(request.member, order.pizza_event)):
            return False
        return super().has_view_permission(request, order)

    def has_change_permission(self, request, order=None):
        """Only give change permission if the user is an organiser"""
        if (order is not None and
                not services.is_organiser(request.member, order.pizza_event)):
            return False
        return super().has_change_permission(request, order)

    def has_delete_permission(self, request, order=None):
        """Only give delete permission if the user is an organiser"""
        if (order is not None and
                not services.is_organiser(request.member, order.pizza_event)):
            return False
        return super().has_delete_permission(request, order)
