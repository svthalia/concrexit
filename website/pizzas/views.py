"""Views provided by the pizzas package"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from payments.models import Payment
from payments.services import create_payment
from .models import Order, PizzaEvent, Product


@login_required
def index(request):
    """ Overview of user order for a pizza event """
    products = Product.available_products.order_by("name")
    if not request.user.has_perm("pizzas.order_restricted_products"):
        products = products.exclude(restricted=True)
    event = PizzaEvent.current()
    try:
        order = Order.objects.get(pizza_event=event, member=request.member)
    except Order.DoesNotExist:
        order = None
    context = {"event": event, "products": products, "order": order}
    return render(request, "pizzas/index.html", context)


@require_http_methods(["POST"])
def cancel_order(request):
    """ View that cancels a user's order """
    if "order" in request.POST:
        try:
            order = get_object_or_404(Order, pk=int(request.POST["order"]))
            if not order.can_be_changed:
                messages.error(request, _("You can no longer cancel."))
            elif order.member == request.member:
                order.delete()
                messages.success(request, _("Your order has been cancelled."))
        except Http404:
            messages.error(request, _("Your order could not be found."))
    return redirect("pizzas:index")


@require_http_methods(["POST"])
def pay_order(request):
    """ View that marks the order as paid using Thalia Pay """
    if "order" in request.POST:
        try:
            order = get_object_or_404(Order, pk=int(request.POST["order"]))
            if order.member == request.member:
                create_payment(order, Payment.TPAY, order.member)
                messages.success(
                    request, _("Your order has been paid with " "Thalia Pay.")
                )
        except Http404:
            messages.error(request, _("Your order could not be found."))
    return redirect("pizzas:index")


@login_required
def order(request):
    """ View that shows the detail of the current order """
    event = PizzaEvent.current()
    if not event:
        return redirect("pizzas:index")

    try:
        order = Order.objects.get(pizza_event=event, member=request.member)
        current_order_locked = not order.can_be_changed
    except Order.DoesNotExist:
        order = None
        current_order_locked = False

    if "product" in request.POST and not current_order_locked:
        productset = Product.available_products.all()
        if not request.user.has_perm("pizzas.order_restricted_products"):
            productset = productset.exclude(restricted=True)
        try:
            product = productset.get(pk=int(request.POST["product"]))
        except Product.DoesNotExist:
            raise Http404("Pizza does not exist")
        if not order:
            order = Order(pizza_event=event, member=request.member)
        order.product = product
        order.save()
    return redirect("pizzas:index")
