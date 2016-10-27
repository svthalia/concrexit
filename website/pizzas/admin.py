from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from .models import Order, PizzaEvent, Product

admin.site.register(Product)


@admin.register(PizzaEvent)
class PizzaEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'orders')

    def orders(self, obj):
        return format_html(_('<strong><a href="{link}">Orders</a></strong>'),
                           link=reverse('pizzas:orders',
                                        kwargs={'event_pk': obj.pk}))


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('pizza_event', 'member_name', 'product', 'paid')
