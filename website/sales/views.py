from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View

from sales import services
from sales.forms import ProductOrderForm
from sales.models.order import Shift, Order, OrderItem
from sales.models.product import ProductListItem

@login_required
def place_order_view(request, *args, **kwargs):
    shift = get_object_or_404(Shift, pk=kwargs["pk"])
    if not shift.selforder:
        # Orders can only be placed by shift managers
        # Time issues are dealt with in the template
        raise PermissionError
    if not shift.user_orders_allowed and request.method == "POST":
        # Forbid POSTing when not in the correct time period
        raise PermissionError
    if shift.locked:
        # You cannot order in a locked shift!
        raise PermissionError

    if request.method == "POST":
        form = ProductOrderForm(shift.product_list, services.is_adult(request.member), request.POST)
        if form.is_valid():
            order = Order(
                created_at=timezone.now(),
                created_by=request.member,
                shift=shift,
                payment=None,
                discount=0.00,
                payer=request.member,
            )
            order.save()
            for fieldname, amount in form.cleaned_data.items():
                if amount is None:
                    continue
                # TODO: deal with age-restricted items
                item = OrderItem(
                    product=form.fields[fieldname].get_productlistitem(),
                    order=order,
                    amount=amount,
                )
                item.save()
            return redirect("sales:order-pay", pk=order.pk)
    else:
        form = ProductOrderForm(shift.product_list, services.is_adult(request.member))

    context = {}
    context["shift"] = shift
    context["items"] = ProductListItem.objects.filter(product_list=shift.product_list)
    context["form"] = form
    context["date_now"] = timezone.now()
    context["formfield"] = context["form"].fields["product_1"]

    return render(request, "sales/order_place.html", context)

@method_decorator(login_required, name="dispatch")
class OrderPaymentView(View):
    def get(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs["pk"])
        if order.payment:
            messages.warning(request, _("This order was already paid for."))
            return redirect("index")
        if order.payer is not None and order.payer != request.member:
            messages.warning(request, _("This order is not yours."))
            return redirect("index")

        order.payer = request.member
        order.save()

        if order.age_restricted and not services.is_adult(request.member):
            messages.error(
                request,
                _(
                    "The age restrictions on this order do not allow you to pay for this order."
                ),
            )
            return redirect("index")

        if (
            order.age_restricted
            and services.is_adult(request.member)
            and order.total_amount == 0
        ):
            messages.success(
                request, _("You have successfully identified yourself for this order.")
            )
            return redirect("index")

        if order.total_amount == 0:
            messages.info(request, _("This order doesn't require payment."))
            return redirect("index")

        return render(request, "sales/order_payment.html", {"order": order})
