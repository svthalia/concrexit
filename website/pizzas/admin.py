from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from .models import Order, PizzaEvent, Product
from events.models import Event

admin.site.register(Product)


@admin.register(PizzaEvent)
class PizzaEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'orders')

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
