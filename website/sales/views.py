from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View

from sales import services
from sales.models.order import Order


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
