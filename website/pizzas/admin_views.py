"""Admin views provided by the pizzas package."""
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from payments.models import Payment
from pizzas.decorators import organiser_only
from pizzas.models import FoodEvent, FoodOrder


@method_decorator(organiser_only, name="dispatch")
class PizzaOrderSummary(TemplateView):
    template_name = "pizzas/admin/summary.html"
    admin = None

    def get_context_data(self, **kwargs):
        event = get_object_or_404(FoodEvent, pk=kwargs.get("pk"))

        context = super().get_context_data(**kwargs)
        context.update(
            {
                **self.admin.admin_site.each_context(self.request),
                "has_delete_permission": False,
                "has_editable_inline_admin_formsets": False,
                "app_label": "pizzas",
                "opts": FoodEvent._meta,
                "is_popup": False,
                "save_as": False,
                "save_on_top": False,
                "title": capfirst(_("order summary")),
                "original": capfirst(_("summary")),
                "food_event": event,
            }
        )

        product_list = {}
        orders = FoodOrder.objects.filter(food_event=event).prefetch_related("product")

        for order in orders:
            if order.product.id not in product_list:
                product_list[order.product.id] = {
                    "name": order.product.name,
                    "price": order.product.price,
                    "amount": 0,
                    "total": 0,
                }
            product_list[order.product.id]["amount"] += 1
            product_list[order.product.id]["total"] += order.product.price

        product_list = sorted(product_list.values(), key=lambda x: x["name"])

        context.update(
            {
                "event": event,
                "product_list": product_list,
                "total_money": sum(map(lambda x: x["total"], product_list)),
                "total_products": len(orders),
            }
        )

        return context


@method_decorator(organiser_only, name="dispatch")
class PizzaOrderDetails(TemplateView):
    template_name = "pizzas/admin/orders.html"
    admin = None

    def get_context_data(self, **kwargs):
        event = get_object_or_404(FoodEvent, pk=kwargs.get("pk"))

        context = super().get_context_data(**kwargs)
        context.update(
            {
                **self.admin.admin_site.each_context(self.request),
                "has_delete_permission": False,
                "has_editable_inline_admin_formsets": False,
                "app_label": "pizzas",
                "opts": FoodEvent._meta,
                "is_popup": False,
                "save_as": False,
                "save_on_top": False,
                "title": capfirst(_("order overview")),
                "original": str(event),
                "food_event": event,
            }
        )

        context.update(
            {
                "event": event,
                "payment": Payment,
                "orders": (
                    FoodOrder.objects.filter(food_event=event)
                    .prefetch_related("member", "product")
                    .order_by("member__first_name")
                ),
            }
        )

        return context
