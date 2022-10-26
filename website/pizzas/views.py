"""Views provided by the pizzas package."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from payments.exceptions import PaymentError
from payments.services import delete_payment

from .models import FoodEvent, FoodOrder, Product


@login_required
def index(request):
    """Overview of user order for a pizza event."""
    products = Product.available_products.order_by("name")
    if not request.user.has_perm("pizzas.order_restricted_products"):
        products = products.exclude(restricted=True)
    event = FoodEvent.current()
    try:
        obj = FoodOrder.objects.get(food_event=event, member=request.member)
    except FoodOrder.DoesNotExist:
        obj = None
    context = {"event": event, "products": products, "order": obj}
    return render(request, "pizzas/index.html", context)


@require_http_methods(["POST"])
def cancel_order(request):
    """View that cancels a user's order."""
    if "order" in request.POST:
        try:
            order = get_object_or_404(FoodOrder, pk=int(request.POST["order"]))
            if not order.can_be_changed:
                messages.error(request, _("You can no longer cancel."))
            elif order.member == request.member:
                try:
                    order.delete()
                    messages.success(request, _("Your order has been cancelled."))
                except PaymentError as e:
                    messages.error(request, str(e))
        except Http404:
            messages.error(request, _("Your order could not be found."))
    return redirect("pizzas:index")


@login_required
def place_order(request):
    """View that shows the detail of the current order."""
    event = FoodEvent.current()
    if not event:
        return redirect("pizzas:index")

    try:
        obj = FoodOrder.objects.get(food_event=event, member=request.member)
        current_order_locked = not obj.can_be_changed
    except FoodOrder.DoesNotExist:
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
            obj = FoodOrder(food_event=event, member=request.member)
        obj.product = product
        if obj.payment:
            try:
                delete_payment(obj, member=request.member, ignore_change_window=True)
            except PaymentError:
                messages.error(
                    request,
                    _("Your order could not be updated because it was already paid."),
                )
                return redirect("pizzas:index")
        obj.save()
    return redirect("pizzas:index")
