"""Views provided by the pizzas package"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from .models import Order, PizzaEvent, Product


@login_required
def index(request):
    """ Overview of user order for a pizza event """
    products = Product.available_products.order_by("name")
    if not request.user.has_perm("pizzas.order_restricted_products"):
        products = products.exclude(restricted=True)
    event = PizzaEvent.current()
    try:
        obj = Order.objects.get(pizza_event=event, member=request.member)
    except Order.DoesNotExist:
        obj = None
    context = {"event": event, "products": products, "order": obj}
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


@login_required
def place_order(request):
    """ View that shows the detail of the current order """
    event = PizzaEvent.current()
    if not event:
        return redirect("pizzas:index")

    try:
        obj = Order.objects.get(pizza_event=event, member=request.member)
        current_order_locked = not obj.can_be_changed
    except Order.DoesNotExist:
        obj = None
        current_order_locked = False

    if "product" in request.POST and not current_order_locked:
        productset = Product.available_products.all()
        if not request.user.has_perm("pizzas.order_restricted_products"):
            productset = productset.exclude(restricted=True)
        try:
            product = productset.get(pk=int(request.POST["product"]))
        except Product.DoesNotExist as e:
            raise Http404("Pizza does not exist") from e
        if not obj:
            obj = Order(pizza_event=event, member=request.member)
        obj.product = product
        obj.save()
    return redirect("pizzas:index")
